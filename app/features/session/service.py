import math
import random

from fastapi import HTTPException, status

from app.features.entity.repo import EntityRepo
from app.features.match.model import Match
from app.features.tournament.repo import TournamentRepo

from .model import Session, SessionStatus
from .repo import MatchRepo, SessionRepo
from .schemas import MatchRead, SessionRead, VoteResponse


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepo,
        match_repo: MatchRepo,
        entity_repo: EntityRepo,
        tournament_repo: TournamentRepo,
    ) -> None:
        self.session_repo = session_repo
        self.match_repo = match_repo
        self.entity_repo = entity_repo
        self.tournament_repo = tournament_repo

    async def start_session(self, tournament_id: int, user_id: int | None) -> SessionRead:
        tournament = await self.tournament_repo.get_by_id(tournament_id)

        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")

        entities = await self.entity_repo.get_all_by_tournament(tournament_id)

        if len(entities) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tournament must have at least 2 entities",
            )

        entity_ids = [e.id for e in entities]
        random.shuffle(entity_ids)

        bracket_size = 1
        while bracket_size < len(entity_ids):
            bracket_size *= 2

        total_rounds = int(math.log2(bracket_size))

        padded = entity_ids + [None] * (bracket_size - len(entity_ids))

        db_session = await self.session_repo.create(
            tournament_id=tournament_id,
            user_id=user_id,
            status=SessionStatus.IN_PROGRESS,
            total_rounds=total_rounds,
            current_round=1,
            current_match_position=0,
        )

        matches_by_round: dict[int, list[Match]] = {}

        # Round 1: pair shuffled entities
        round_1_matches = []
        for i in range(bracket_size // 2):
            e1 = padded[i * 2]
            e2 = padded[i * 2 + 1]
            is_bye = e2 is None
            match = Match(
                session_id=db_session.id,
                round=1,
                position=i,
                entity_1_id=e1,
                entity_2_id=e2,
                is_bye=is_bye,
            )
            round_1_matches.append(match)

        await self.match_repo.create_bulk(round_1_matches)
        matches_by_round[1] = round_1_matches

        # Rounds 2..total_rounds: build from previous round
        for r in range(2, total_rounds + 1):
            prev = matches_by_round[r - 1]
            current_matches = []

            for i in range(len(prev) // 2):
                child_a = prev[i * 2]
                child_b = prev[i * 2 + 1]

                # Pre-fill slots from bye winners
                e1 = child_a.entity_1_id if child_a.is_bye else None
                e2 = child_b.entity_1_id if child_b.is_bye else None

                # A match is a bye if exactly one slot is filled
                is_bye = (e1 is not None) != (e2 is not None)

                match = Match(
                    session_id=db_session.id,
                    round=r,
                    position=i,
                    entity_1_id=e1,
                    entity_2_id=e2,
                    is_bye=is_bye,
                )
                current_matches.append(match)

            await self.match_repo.create_bulk(current_matches)

            # Link children to parent matches
            for i, prev_match in enumerate(prev):
                prev_match.next_match_id = current_matches[i // 2].id

            matches_by_round[r] = current_matches

        # Propagate cascading byes (a bye match's winner goes up)
        for r in range(2, total_rounds + 1):
            for match in matches_by_round[r]:
                if match.is_bye and match.next_match_id is not None:
                    winner = match.entity_1_id or match.entity_2_id
                    # Find the next match in the next round
                    next_round_matches = matches_by_round.get(r + 1)
                    if next_round_matches:
                        parent = next_round_matches[match.position // 2]
                        if match.position % 2 == 0:
                            parent.entity_1_id = winner
                        else:
                            parent.entity_2_id = winner
                        # Check if parent becomes a bye too
                        parent.is_bye = (parent.entity_1_id is not None) != (parent.entity_2_id is not None)

        # Find first non-bye match
        first_match = None
        for r in range(1, total_rounds + 1):
            for match in matches_by_round[r]:
                if not match.is_bye and match.entity_1_id is not None and match.entity_2_id is not None:
                    first_match = match
                    break
            if first_match:
                break

        if first_match:
            db_session.current_round = first_match.round
            db_session.current_match_position = first_match.position

        await self.session_repo.commit()

        # Reload to get full relationships
        loaded_session = await self.session_repo.get_by_id(db_session.id)
        return self._to_session_read(loaded_session)

    async def get_session(self, session_id: int) -> SessionRead:
        db_session = await self.session_repo.get_by_id(session_id)

        if not db_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        return self._to_session_read(db_session)

    async def vote(self, session_id: int, user_id: int | None, chosen_entity_id: int) -> VoteResponse:
        db_session = await self.session_repo.get_by_id(session_id)

        if not db_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        if db_session.status == SessionStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already completed")

        if db_session.user_id is not None and db_session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Find current match
        current_match = None
        for m in db_session.matches:
            if m.round == db_session.current_round and m.position == db_session.current_match_position:
                current_match = m
                break

        if not current_match:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No current match found")

        # Validate vote
        if chosen_entity_id not in (current_match.entity_1_id, current_match.entity_2_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entity choice")

        # Place winner into next match
        if current_match.next_match_id is not None:
            next_match = None
            for m in db_session.matches:
                if m.id == current_match.next_match_id:
                    next_match = m
                    break

            if next_match:
                if current_match.position % 2 == 0:
                    next_match.entity_1_id = chosen_entity_id
                else:
                    next_match.entity_2_id = chosen_entity_id

        # Find next votable match
        next_votable = self._find_next_votable(
            db_session.matches,
            db_session.current_round,
            db_session.current_match_position,
            db_session.total_rounds,
        )

        is_completed = False
        if next_votable is None:
            db_session.status = SessionStatus.COMPLETED
            db_session.winner_entity_id = chosen_entity_id
            is_completed = True
        else:
            db_session.current_round = next_votable.round
            db_session.current_match_position = next_votable.position

        await self.session_repo.commit()

        # Reload for fresh relationships
        loaded_session = await self.session_repo.get_by_id(session_id)
        return VoteResponse(
            session=self._to_session_read(loaded_session),
            is_completed=is_completed,
        )

    def _find_next_votable(
        self,
        matches: list[Match],
        current_round: int,
        current_position: int,
        total_rounds: int,
    ) -> Match | None:
        sorted_matches = sorted(matches, key=lambda m: (m.round, m.position))

        for m in sorted_matches:
            # Skip matches at or before the current position
            if m.round < current_round:
                continue
            if m.round == current_round and m.position <= current_position:
                continue
            # A match is votable if it has both entities and is not a bye
            if not m.is_bye and m.entity_1_id is not None and m.entity_2_id is not None:
                return m

        return None

    def _to_session_read(self, db_session: Session) -> SessionRead:
        current_match = None
        for m in db_session.matches:
            if m.round == db_session.current_round and m.position == db_session.current_match_position:
                current_match = MatchRead.model_validate(m)
                break

        return SessionRead(
            id=db_session.id,
            tournament_id=db_session.tournament_id,
            user_id=db_session.user_id,
            status=db_session.status.value,
            total_rounds=db_session.total_rounds,
            current_round=db_session.current_round,
            current_match_position=db_session.current_match_position,
            winner_entity_id=db_session.winner_entity_id,
            current_match=current_match,
        )

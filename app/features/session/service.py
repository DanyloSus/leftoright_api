import random

from fastapi import HTTPException, status

from app.features.entity.repo import EntityRepo
from app.features.match.model import Match
from app.features.match.service import MatchService
from app.features.tournament.repo import TournamentRepo

from .model import Session, SessionStatus
from .repo import SessionRepo
from .schemas import MatchRead, SessionRead, VoteResponse


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepo,
        match_service: MatchService,
        entity_repo: EntityRepo,
        tournament_repo: TournamentRepo,
    ) -> None:
        self.session_repo = session_repo
        self.match_service = match_service
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

        entity_ids = [entity.id for entity in entities]
        random.shuffle(entity_ids)

        bracket_size = 1
        total_rounds = 0
        while bracket_size < len(entity_ids):
            bracket_size *= 2
            total_rounds += 1

        padded_entity_ids = entity_ids + [None] * (bracket_size - len(entity_ids))

        session = await self.session_repo.create(
            tournament_id=tournament_id,
            user_id=user_id,
            status=SessionStatus.IN_PROGRESS,
            total_rounds=total_rounds,
            current_round=1,
            current_match_position=0,
        )

        matches_by_round = {}

        first_round = self.match_service.build_first_round(
            session.id, padded_entity_ids, bracket_size,
        )
        await self.match_service.create_bulk(first_round)
        matches_by_round[1] = first_round

        for round_number in range(2, total_rounds + 1):
            previous_matches = matches_by_round[round_number - 1]
            current_matches = self.match_service.build_next_round(
                session.id, round_number, previous_matches,
            )
            await self.match_service.create_bulk(current_matches)
            self.match_service.link_to_parent(previous_matches, current_matches)
            matches_by_round[round_number] = current_matches

        self.match_service.propagate_cascading_byes(matches_by_round, total_rounds)

        first_votable = self.match_service.find_first_votable(matches_by_round, total_rounds)
        if first_votable:
            session.current_round = first_votable.round
            session.current_match_position = first_votable.position

        await self.session_repo.commit()

        loaded_session = await self.session_repo.get_by_id(session.id)
        return self._to_session_read(loaded_session)

    async def get_session(self, session_id: int) -> SessionRead:
        session = await self.session_repo.get_by_id(session_id)

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        return self._to_session_read(session)

    async def vote(self, session_id: int, user_id: int | None, chosen_entity_id: int) -> VoteResponse:
        session = await self.session_repo.get_by_id(session_id)

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        if session.status == SessionStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already completed")

        if session.user_id is not None and session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        current_match = None
        for match in session.matches:
            if match.round == session.current_round and match.position == session.current_match_position:
                current_match = match
                break

        if not current_match:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No current match found")

        if chosen_entity_id not in (current_match.entity_1_id, current_match.entity_2_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entity choice")

        if current_match.next_match_id is not None:
            next_match = None
            for match in session.matches:
                if match.id == current_match.next_match_id:
                    next_match = match
                    break

            if next_match:
                if current_match.position % 2 == 0:
                    next_match.entity_1_id = chosen_entity_id
                else:
                    next_match.entity_2_id = chosen_entity_id

        next_votable = self._find_next_votable(
            session.matches,
            session.current_round,
            session.current_match_position,
        )

        is_completed = False
        if next_votable is None:
            session.status = SessionStatus.COMPLETED
            session.winner_entity_id = chosen_entity_id
            is_completed = True
        else:
            session.current_round = next_votable.round
            session.current_match_position = next_votable.position

        await self.session_repo.commit()

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
    ) -> Match | None:
        sorted_matches = sorted(matches, key=lambda match: (match.round, match.position))

        for match in sorted_matches:
            if match.round < current_round:
                continue
            if match.round == current_round and match.position <= current_position:
                continue
            if not match.is_bye and match.entity_1_id is not None and match.entity_2_id is not None:
                return match

        return None

    def _to_session_read(self, session: Session) -> SessionRead:
        current_match = None
        for match in session.matches:
            if match.round == session.current_round and match.position == session.current_match_position:
                current_match = MatchRead.model_validate(match)
                break

        return SessionRead(
            id=session.id,
            tournament_id=session.tournament_id,
            user_id=session.user_id,
            status=session.status.value,
            total_rounds=session.total_rounds,
            current_round=session.current_round,
            current_match_position=session.current_match_position,
            winner_entity_id=session.winner_entity_id,
            current_match=current_match,
        )

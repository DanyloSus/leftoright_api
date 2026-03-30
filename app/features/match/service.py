from .model import Match
from .repo import MatchRepo


class MatchService:
    def __init__(self, repo: MatchRepo) -> None:
        self.repo = repo

    async def create_bulk(self, matches: list[Match]) -> list[Match]:
        return await self.repo.create_bulk(matches)

    def build_first_round(
        self,
        session_id: int,
        padded_entity_ids: list[int | None],
        bracket_size: int,
    ) -> list[Match]:
        matches = []

        for position in range(bracket_size // 2):
            entity_1_id = padded_entity_ids[position * 2]
            entity_2_id = padded_entity_ids[position * 2 + 1]

            matches.append(Match(
                session_id=session_id,
                round=1,
                position=position,
                entity_1_id=entity_1_id,
                entity_2_id=entity_2_id,
                is_bye=entity_2_id is None,
            ))

        return matches

    def build_next_round(
        self,
        session_id: int,
        round_number: int,
        previous_matches: list[Match],
    ) -> list[Match]:
        current_matches = []

        for position in range(len(previous_matches) // 2):
            child_a = previous_matches[position * 2]
            child_b = previous_matches[position * 2 + 1]

            entity_1_id = child_a.entity_1_id if child_a.is_bye else None
            entity_2_id = child_b.entity_1_id if child_b.is_bye else None

            current_matches.append(Match(
                session_id=session_id,
                round=round_number,
                position=position,
                entity_1_id=entity_1_id,
                entity_2_id=entity_2_id,
                is_bye=(entity_1_id is not None) != (entity_2_id is not None),
            ))

        return current_matches

    def link_to_parent(self, previous_matches: list[Match], parent_matches: list[Match]) -> None:
        for index, previous_match in enumerate(previous_matches):
            previous_match.next_match_id = parent_matches[index // 2].id

    def propagate_cascading_byes(
        self,
        matches_by_round: dict[int, list[Match]],
        total_rounds: int,
    ) -> None:
        for round_number in range(2, total_rounds + 1):
            for match in matches_by_round[round_number]:
                if not match.is_bye or match.next_match_id is None:
                    continue

                winner_id = match.entity_1_id or match.entity_2_id
                next_round_matches = matches_by_round.get(round_number + 1)

                if not next_round_matches:
                    continue

                parent = next_round_matches[match.position // 2]

                if match.position % 2 == 0:
                    parent.entity_1_id = winner_id
                else:
                    parent.entity_2_id = winner_id

                parent.is_bye = (parent.entity_1_id is not None) != (parent.entity_2_id is not None)

    def find_first_votable(
        self,
        matches_by_round: dict[int, list[Match]],
        total_rounds: int,
    ) -> Match | None:
        for round_number in range(1, total_rounds + 1):
            for match in matches_by_round[round_number]:
                if not match.is_bye and match.entity_1_id is not None and match.entity_2_id is not None:
                    return match
        return None

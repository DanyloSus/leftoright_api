from pydantic import BaseModel

from app.features.entity.schemas import EntityRead


class MatchRead(BaseModel):
    id: int
    round: int
    position: int
    entity_1: EntityRead | None
    entity_2: EntityRead | None
    is_bye: bool
    next_match_id: int | None
    winner_entity_id: int | None
    status: str

    model_config = {"from_attributes": True}


class SessionRead(BaseModel):
    id: int
    tournament_id: int
    user_id: int | None
    status: str
    total_rounds: int
    current_round: int
    current_match_position: int
    winner_entity_id: int | None
    current_match: MatchRead | None

    model_config = {"from_attributes": True}


class VoteRequest(BaseModel):
    chosen_entity_id: int


class VoteResponse(BaseModel):
    session: SessionRead
    is_completed: bool

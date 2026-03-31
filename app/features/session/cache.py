import json
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.match.model import MatchStatus
from app.features.session.model import SessionStatus
from configs.redis_client import redis_client

_TTL = 10  # seconds


@dataclass
class EntitySnapshot:
    id: int
    name: str
    youtube_url: str | None
    tournament_id: int


@dataclass
class MatchSnapshot:
    id: int
    round: int
    position: int
    entity_1_id: int | None
    entity_2_id: int | None
    entity_1: EntitySnapshot | None
    entity_2: EntitySnapshot | None
    is_bye: bool
    status: MatchStatus
    winner_entity_id: int | None
    next_match_id: int | None


@dataclass
class SessionSnapshot:
    id: int
    status: SessionStatus
    total_rounds: int
    current_round: int
    current_match_position: int
    winner_entity_id: int | None
    matches: list[MatchSnapshot]


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _entity_to_dict(entity) -> dict | None:
    if entity is None:
        return None
    return {
        "id": entity.id,
        "name": entity.name,
        "youtube_url": entity.youtube_url,
        "tournament_id": entity.tournament_id,
    }


def _match_to_dict(match) -> dict:
    status = match.status if isinstance(match.status, str) else match.status.value
    return {
        "id": match.id,
        "round": match.round,
        "position": match.position,
        "entity_1_id": match.entity_1_id,
        "entity_2_id": match.entity_2_id,
        "entity_1": _entity_to_dict(match.entity_1),
        "entity_2": _entity_to_dict(match.entity_2),
        "is_bye": match.is_bye,
        "status": status,
        "winner_entity_id": match.winner_entity_id,
        "next_match_id": match.next_match_id,
    }


def _session_to_dict(session) -> dict:
    status = session.status if isinstance(session.status, str) else session.status.value
    return {
        "id": session.id,
        "status": status,
        "total_rounds": session.total_rounds,
        "current_round": session.current_round,
        "current_match_position": session.current_match_position,
        "winner_entity_id": session.winner_entity_id,
        "matches": [_match_to_dict(m) for m in session.matches],
    }


# ---------------------------------------------------------------------------
# Deserialisation helpers
# ---------------------------------------------------------------------------


def _dict_to_entity(d: dict | None) -> EntitySnapshot | None:
    if d is None:
        return None
    return EntitySnapshot(
        id=d["id"],
        name=d["name"],
        youtube_url=d.get("youtube_url"),
        tournament_id=d["tournament_id"],
    )


def _dict_to_match(d: dict) -> MatchSnapshot:
    return MatchSnapshot(
        id=d["id"],
        round=d["round"],
        position=d["position"],
        entity_1_id=d["entity_1_id"],
        entity_2_id=d["entity_2_id"],
        entity_1=_dict_to_entity(d["entity_1"]),
        entity_2=_dict_to_entity(d["entity_2"]),
        is_bye=d["is_bye"],
        status=MatchStatus(d["status"]),
        winner_entity_id=d["winner_entity_id"],
        next_match_id=d["next_match_id"],
    )


def _dict_to_snapshot(d: dict) -> SessionSnapshot:
    return SessionSnapshot(
        id=d["id"],
        status=SessionStatus(d["status"]),
        total_rounds=d["total_rounds"],
        current_round=d["current_round"],
        current_match_position=d["current_match_position"],
        winner_entity_id=d["winner_entity_id"],
        matches=[_dict_to_match(m) for m in d["matches"]],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _cache_key(session_id: int) -> str:
    return f"cache:session:{session_id}"


async def get_cached_session(
    session_id: int, db: AsyncSession
) -> SessionSnapshot | None:
    cached = await redis_client.get(_cache_key(session_id))
    if cached:
        return _dict_to_snapshot(json.loads(cached))

    from app.features.session.repo import SessionRepo  # local import avoids circular

    session = await SessionRepo(db).get_by_id(session_id)
    if session is None:
        return None

    d = _session_to_dict(session)
    await redis_client.setex(_cache_key(session_id), _TTL, json.dumps(d))
    return _dict_to_snapshot(d)


async def invalidate_session_cache(session_id: int) -> None:
    await redis_client.delete(_cache_key(session_id))

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.match.model import Match, MatchStatus
from configs.session import AsyncSessionFactory

from .connection_manager import ConnectionManager
from .model import Session, SessionStatus
from .repo import SessionRepo

manager = ConnectionManager()


async def session_websocket(websocket: WebSocket, session_id: int) -> None:
    await websocket.accept()

    player_id: str | None = None
    try:
        first = await websocket.receive_json()
        event_type = first.get("type")

        if event_type not in ("JOIN_SESSION", "RECONNECT_SESSION"):
            await websocket.send_json({"type": "ERROR", "code": "INVALID_FIRST_MESSAGE"})
            await websocket.close()
            return

        player_id = first.get("playerId")
        if not player_id:
            await websocket.send_json({"type": "ERROR", "code": "MISSING_PLAYER_ID"})
            await websocket.close()
            return

        async with AsyncSessionFactory() as db:
            if event_type == "JOIN_SESSION":
                ok = await _handle_join(websocket, session_id, player_id, first.get("name"), db)
            else:
                ok = await _handle_reconnect(websocket, session_id, player_id, db)

        if not ok:
            return

        async for message in websocket.iter_json():
            msg_type = message.get("type")
            async with AsyncSessionFactory() as db:
                if msg_type == "VOTE":
                    await _handle_vote(websocket, session_id, player_id, message, db)
                elif msg_type == "START_SESSION":
                    await _handle_start_session(websocket, session_id, player_id, db)
                elif msg_type == "START_NEXT_MATCH":
                    await _handle_start_next_match(websocket, session_id, player_id, db)
                elif msg_type == "HOST_CONTROL":
                    await _handle_host_control(websocket, session_id, player_id, message)
                else:
                    await websocket.send_json({"type": "ERROR", "code": "UNKNOWN_EVENT"})

    except WebSocketDisconnect:
        pass
    finally:
        if player_id:
            await _handle_disconnect(session_id, player_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_session(db: AsyncSession, session_id: int) -> Session | None:
    repo = SessionRepo(db)
    return await repo.get_by_id(session_id)


def _current_match(session: Session) -> Match | None:
    for m in session.matches:
        if m.round == session.current_round and m.position == session.current_match_position:
            return m
    return None


def _match_payload(match: Match) -> dict:
    return {
        "id": match.id,
        "round": match.round,
        "position": match.position,
        "entity_1": _entity_payload(match.entity_1),
        "entity_2": _entity_payload(match.entity_2),
        "is_bye": match.is_bye,
        "status": match.status,
        "winner_entity_id": match.winner_entity_id,
    }


def _entity_payload(entity) -> dict | None:
    if entity is None:
        return None
    return {
        "id": entity.id,
        "name": entity.name,
        "youtube_url": entity.youtube_url,
        "tournament_id": entity.tournament_id,
    }


def _session_payload(session: Session) -> dict:
    return {
        "id": session.id,
        "status": session.status.value,
        "total_rounds": session.total_rounds,
        "current_round": session.current_round,
        "current_match_position": session.current_match_position,
        "winner_entity_id": session.winner_entity_id,
    }


def _find_next_votable(
    matches: list[Match],
    current_round: int,
    current_position: int,
) -> Match | None:
    sorted_matches = sorted(matches, key=lambda m: (m.round, m.position))
    for m in sorted_matches:
        if m.round < current_round:
            continue
        if m.round == current_round and m.position <= current_position:
            continue
        if not m.is_bye and m.entity_1_id is not None and m.entity_2_id is not None:
            return m
    return None


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

async def _handle_join(
    ws: WebSocket,
    session_id: int,
    player_id: str,
    name: str | None,
    db: AsyncSession,
) -> bool:
    session = await _load_session(db, session_id)
    if not session:
        await ws.send_json({"type": "ERROR", "code": "NOT_FOUND"})
        await ws.close()
        return False

    is_host = manager.connect(session_id, player_id, ws, name)
    cur = _current_match(session)

    await ws.send_json({
        "type": "SESSION_STATE",
        "session": _session_payload(session),
        "currentMatch": _match_payload(cur) if cur else None,
        "players": manager.get_players_list(session_id),
        "votes": manager.get_votes(session_id),
        "isHost": is_host,
    })

    await manager.broadcast(session_id, {
        "type": "PLAYER_JOINED",
        "player": {"id": player_id, "name": name, "isOnline": True},
    }, exclude=player_id)
    return True


async def _handle_reconnect(
    ws: WebSocket,
    session_id: int,
    player_id: str,
    db: AsyncSession,
) -> bool:
    session = await _load_session(db, session_id)
    if not session:
        await ws.send_json({"type": "ERROR", "code": "NOT_FOUND"})
        await ws.close()
        return False

    is_host = manager.connect(session_id, player_id, ws)
    cur = _current_match(session)

    await ws.send_json({
        "type": "SESSION_STATE",
        "session": _session_payload(session),
        "currentMatch": _match_payload(cur) if cur else None,
        "players": manager.get_players_list(session_id),
        "votes": manager.get_votes(session_id),
        "isHost": is_host,
    })
    return True


async def _handle_vote(
    ws: WebSocket,
    session_id: int,
    player_id: str,
    data: dict,
    db: AsyncSession,
) -> None:
    session = await _load_session(db, session_id)
    if not session or session.status != SessionStatus.IN_PROGRESS:
        await ws.send_json({"type": "ERROR", "code": "SESSION_NOT_ACTIVE"})
        return

    cur = _current_match(session)
    if not cur:
        await ws.send_json({"type": "ERROR", "code": "NO_CURRENT_MATCH"})
        return

    entity_id = data.get("entityId")
    if entity_id not in (cur.entity_1_id, cur.entity_2_id):
        await ws.send_json({"type": "ERROR", "code": "INVALID_ENTITY"})
        return

    if manager.has_voted(session_id, player_id):
        await ws.send_json({"type": "ERROR", "code": "ALREADY_VOTED"})
        return

    all_voted = manager.record_vote(session_id, player_id, entity_id)

    await manager.broadcast(session_id, {
        "type": "MATCH_UPDATED",
        "matchId": cur.id,
        "votes": manager.get_vote_counts(session_id),
    })

    if all_voted:
        await _finish_voting(session_id, session, cur, db)


async def _finish_voting(
    session_id: int,
    session: Session,
    current_match: Match,
    db: AsyncSession,
) -> None:
    vote_counts = manager.get_vote_counts(session_id)

    # Determine winner: most votes; tie → entity_1
    e1_votes = vote_counts.get(current_match.entity_1_id, 0)
    e2_votes = vote_counts.get(current_match.entity_2_id, 0)
    winner_id = current_match.entity_1_id if e1_votes >= e2_votes else current_match.entity_2_id

    await manager.broadcast(session_id, {"type": "VOTING_ENDED", "matchId": current_match.id})

    # Persist winner on the match
    current_match.winner_entity_id = winner_id
    current_match.status = MatchStatus.FINISHED

    # Propagate winner to next match
    if current_match.next_match_id is not None:
        next_match = None
        for m in session.matches:
            if m.id == current_match.next_match_id:
                next_match = m
                break
        if next_match:
            if current_match.position % 2 == 0:
                next_match.entity_1_id = winner_id
            else:
                next_match.entity_2_id = winner_id

    old_round = session.current_round

    # Advance cursor
    next_votable = _find_next_votable(
        session.matches,
        session.current_round,
        session.current_match_position,
    )

    is_completed = False
    if next_votable is None:
        session.status = SessionStatus.COMPLETED
        session.winner_entity_id = winner_id
        is_completed = True
    else:
        session.current_round = next_votable.round
        session.current_match_position = next_votable.position

    await db.commit()

    await manager.broadcast(session_id, {
        "type": "MATCH_FINISHED",
        "matchId": current_match.id,
        "winner_entity_id": winner_id,
    })

    if not is_completed and next_votable and next_votable.round != old_round:
        await manager.broadcast(session_id, {"type": "ROUND_FINISHED", "round": old_round})
        await manager.broadcast(session_id, {"type": "ROUND_STARTED", "round": next_votable.round})

    if is_completed:
        await manager.broadcast(session_id, {
            "type": "SESSION_FINISHED",
            "winner_entity_id": winner_id,
        })

    manager.clear_votes(session_id)


async def _handle_start_session(
    ws: WebSocket,
    session_id: int,
    player_id: str,
    db: AsyncSession,
) -> None:
    if not manager.is_host(session_id, player_id):
        await ws.send_json({"type": "ERROR", "code": "NOT_HOST"})
        return

    session = await _load_session(db, session_id)
    if not session:
        await ws.send_json({"type": "ERROR", "code": "NOT_FOUND"})
        return

    await manager.broadcast(session_id, {"type": "SESSION_STARTED"})

    cur = _current_match(session)
    if cur:
        await manager.broadcast(session_id, {
            "type": "MATCH_STARTED",
            "match": _match_payload(cur),
            "is_bye": cur.is_bye,
        })
        if not cur.is_bye:
            await manager.broadcast(session_id, {"type": "VOTING_STARTED", "matchId": cur.id})


async def _handle_start_next_match(
    ws: WebSocket,
    session_id: int,
    player_id: str,
    db: AsyncSession,
) -> None:
    if not manager.is_host(session_id, player_id):
        await ws.send_json({"type": "ERROR", "code": "NOT_HOST"})
        return

    session = await _load_session(db, session_id)
    if not session:
        await ws.send_json({"type": "ERROR", "code": "NOT_FOUND"})
        return

    cur = _current_match(session)
    if not cur:
        await ws.send_json({"type": "ERROR", "code": "NO_CURRENT_MATCH"})
        return

    await manager.broadcast(session_id, {
        "type": "MATCH_STARTED",
        "match": _match_payload(cur),
        "is_bye": cur.is_bye,
    })

    if not cur.is_bye:
        manager.clear_votes(session_id)
        await manager.broadcast(session_id, {"type": "VOTING_STARTED", "matchId": cur.id})


async def _handle_host_control(
    ws: WebSocket,
    session_id: int,
    player_id: str,
    data: dict,
) -> None:
    if not manager.is_host(session_id, player_id):
        await ws.send_json({"type": "ERROR", "code": "NOT_HOST"})
        return

    await manager.broadcast(session_id, {
        "type": "HOST_STATE_CHANGED",
        "state": data.get("state", {}),
    })


async def _handle_disconnect(session_id: int, player_id: str) -> None:
    manager.disconnect(session_id, player_id)
    await manager.broadcast(session_id, {
        "type": "PLAYER_LEFT",
        "playerId": player_id,
    })

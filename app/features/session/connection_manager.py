import asyncio
import json

from fastapi import WebSocket

from configs.redis_client import redis_client

_PLAYERS = "ws:{sid}:players"  # Hash: player_id → json(PlayerInfo)
_VOTES = "ws:{sid}:votes"  # Hash: player_id → entity_id
_HOST = "ws:{sid}:host"  # String: player_id
_CHAN = "ws:{sid}:chan"  # Pub/Sub channel


class ConnectionManager:
    def __init__(self) -> None:
        # WebSocket objects are process-local and cannot be stored in Redis.
        self._connections: dict[int, dict[str, WebSocket]] = {}
        self._listener_tasks: dict[int, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(
        self,
        session_id: int,
        player_id: str,
        ws: WebSocket,
        name: str | None = None,
    ) -> bool:
        """Register a player. Returns True if this player is the host."""
        if session_id not in self._connections:
            self._connections[session_id] = {}
        self._connections[session_id][player_id] = ws

        # Update player record in Redis
        player_key = _PLAYERS.format(sid=session_id)
        existing = await redis_client.hget(player_key, player_id)
        if existing:
            info = json.loads(existing)
            info["is_online"] = True
        else:
            info = {"id": player_id, "name": name, "is_online": True}
        await redis_client.hset(player_key, player_id, json.dumps(info))

        # SETNX: only sets if key doesn't exist — first connector becomes host
        host_key = _HOST.format(sid=session_id)
        await redis_client.setnx(host_key, player_id)
        is_host = (await redis_client.get(host_key)) == player_id

        # Start pub/sub listener for this session on this worker if needed
        if session_id not in self._listener_tasks:
            self._listener_tasks[session_id] = asyncio.create_task(
                self._listen(session_id)
            )

        return is_host

    async def disconnect(self, session_id: int, player_id: str) -> None:
        """Mark player offline; keep their record so they can rejoin."""
        room = self._connections.get(session_id, {})
        room.pop(player_id, None)
        if not room:
            self._connections.pop(session_id, None)
            task = self._listener_tasks.pop(session_id, None)
            if task:
                task.cancel()

        player_key = _PLAYERS.format(sid=session_id)
        existing = await redis_client.hget(player_key, player_id)
        if existing:
            info = json.loads(existing)
            info["is_online"] = False
            await redis_client.hset(player_key, player_id, json.dumps(info))

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def broadcast(
        self,
        session_id: int,
        message: dict,
        exclude: str | None = None,
    ) -> None:
        """Publish to Redis so all workers deliver to their local connections."""
        payload = json.dumps({"msg": message, "exclude": exclude})
        await redis_client.publish(_CHAN.format(sid=session_id), payload)

    async def send_to(self, session_id: int, player_id: str, message: dict) -> None:
        """Best-effort direct send to a locally-held connection."""
        ws = self._connections.get(session_id, {}).get(player_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def _listen(self, session_id: int) -> None:
        """Background task: subscribe to the session channel and fan out messages."""
        channel = _CHAN.format(sid=session_id)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for raw in pubsub.listen():
                if raw["type"] != "message":
                    continue
                data = json.loads(raw["data"])
                message = data["msg"]
                exclude = data.get("exclude")
                for pid, ws in list(self._connections.get(session_id, {}).items()):
                    if pid == exclude:
                        continue
                    try:
                        await ws.send_json(message)
                    except Exception:
                        pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    # ------------------------------------------------------------------
    # Votes
    # ------------------------------------------------------------------

    async def record_vote(
        self, session_id: int, player_id: str, entity_id: int
    ) -> bool:
        """Record vote. Returns True when all online players have voted."""
        votes_key = _VOTES.format(sid=session_id)
        await redis_client.hset(votes_key, player_id, entity_id)

        players_raw = await redis_client.hgetall(_PLAYERS.format(sid=session_id))
        votes_raw = await redis_client.hgetall(votes_key)

        online = {pid for pid, v in players_raw.items() if json.loads(v)["is_online"]}
        return online.issubset(votes_raw.keys())

    async def has_voted(self, session_id: int, player_id: str) -> bool:
        return bool(
            await redis_client.hexists(_VOTES.format(sid=session_id), player_id)
        )

    async def clear_votes(self, session_id: int) -> None:
        await redis_client.delete(_VOTES.format(sid=session_id))

    async def get_vote_counts(self, session_id: int) -> dict[int, int]:
        raw = await redis_client.hgetall(_VOTES.format(sid=session_id))
        counts: dict[int, int] = {}
        for eid_str in raw.values():
            eid = int(eid_str)
            counts[eid] = counts.get(eid, 0) + 1
        return counts

    async def get_votes(self, session_id: int) -> dict[str, int]:
        raw = await redis_client.hgetall(_VOTES.format(sid=session_id))
        return {pid: int(eid) for pid, eid in raw.items()}

    # ------------------------------------------------------------------
    # Players / host
    # ------------------------------------------------------------------

    async def is_host(self, session_id: int, player_id: str) -> bool:
        return (await redis_client.get(_HOST.format(sid=session_id))) == player_id

    async def get_players_list(self, session_id: int) -> list[dict]:
        raw = await redis_client.hgetall(_PLAYERS.format(sid=session_id))
        result = []
        for v in raw.values():
            p = json.loads(v)
            result.append(
                {"id": p["id"], "name": p["name"], "isOnline": p["is_online"]}
            )
        return result


manager = ConnectionManager()

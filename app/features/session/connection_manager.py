from dataclasses import dataclass, field
from fastapi import WebSocket


@dataclass
class PlayerInfo:
    id: str
    name: str | None
    is_online: bool


@dataclass
class SessionRoom:
    players: dict[str, PlayerInfo] = field(default_factory=dict)
    connections: dict[str, WebSocket] = field(default_factory=dict)
    votes: dict[str, int] = field(default_factory=dict)  # playerId -> entityId
    host_player_id: str | None = None


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[int, SessionRoom] = {}

    def _get_or_create_room(self, session_id: int) -> SessionRoom:
        if session_id not in self._rooms:
            self._rooms[session_id] = SessionRoom()
        return self._rooms[session_id]

    def connect(self, session_id: int, player_id: str, ws: WebSocket, name: str | None = None) -> bool:
        """Register a player connection. Returns True if this player is the host."""
        room = self._get_or_create_room(session_id)
        room.connections[player_id] = ws
        if player_id in room.players:
            room.players[player_id].is_online = True
        else:
            room.players[player_id] = PlayerInfo(id=player_id, name=name, is_online=True)
        if room.host_player_id is None:
            room.host_player_id = player_id
            return True
        return room.host_player_id == player_id

    def disconnect(self, session_id: int, player_id: str) -> None:
        """Mark player as offline but keep their info in the room."""
        room = self._rooms.get(session_id)
        if not room:
            return
        room.connections.pop(player_id, None)
        if player_id in room.players:
            room.players[player_id].is_online = False

    async def broadcast(self, session_id: int, message: dict, exclude: str | None = None) -> None:
        room = self._rooms.get(session_id)
        if not room:
            return
        for player_id, ws in list(room.connections.items()):
            if player_id == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def send_to(self, session_id: int, player_id: str, message: dict) -> None:
        room = self._rooms.get(session_id)
        if not room:
            return
        ws = room.connections.get(player_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    def record_vote(self, session_id: int, player_id: str, entity_id: int) -> bool:
        """Record a vote. Returns True if all connected players have now voted."""
        room = self._rooms.get(session_id)
        if not room:
            return False
        room.votes[player_id] = entity_id
        online_players = {pid for pid, info in room.players.items() if info.is_online}
        return online_players.issubset(room.votes.keys())

    def has_voted(self, session_id: int, player_id: str) -> bool:
        room = self._rooms.get(session_id)
        if not room:
            return False
        return player_id in room.votes

    def clear_votes(self, session_id: int) -> None:
        room = self._rooms.get(session_id)
        if room:
            room.votes.clear()

    def get_vote_counts(self, session_id: int) -> dict[int, int]:
        """Returns {entityId: voteCount} for the current match."""
        room = self._rooms.get(session_id)
        if not room:
            return {}
        counts: dict[int, int] = {}
        for entity_id in room.votes.values():
            counts[entity_id] = counts.get(entity_id, 0) + 1
        return counts

    def get_votes(self, session_id: int) -> dict[str, int]:
        """Returns {playerId: entityId}."""
        room = self._rooms.get(session_id)
        return dict(room.votes) if room else {}

    def is_host(self, session_id: int, player_id: str) -> bool:
        room = self._rooms.get(session_id)
        return room is not None and room.host_player_id == player_id

    def get_players_list(self, session_id: int) -> list[dict]:
        room = self._rooms.get(session_id)
        if not room:
            return []
        return [
            {"id": p.id, "name": p.name, "isOnline": p.is_online}
            for p in room.players.values()
        ]


manager = ConnectionManager()

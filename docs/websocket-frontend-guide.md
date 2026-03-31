# WebSocket Event System — Frontend Integration Guide

## Connection

```
ws://localhost:8000/api/sessions/{sessionId}/ws
```

The first message **must** be `JOIN_SESSION` or `RECONNECT_SESSION`. Any other message closes the connection.

---

## TypeScript Types

```ts
// ── Entities & Matches ──────────────────────────────────────

interface Entity {
  id: number;
  name: string;
  youtube_url: string | null;
  tournament_id: number;
}

interface Match {
  id: number;
  round: number;
  position: number;
  entity_1: Entity | null;
  entity_2: Entity | null;
  is_bye: boolean;
  status: "PENDING" | "VOTING" | "FINISHED";
  winner_entity_id: number | null;
}

// ── Session ─────────────────────────────────────────────────

interface SessionInfo {
  id: number;
  status: "waiting" | "in_progress" | "paused" | "finished" | "completed";
  total_rounds: number;
  current_round: number;
  current_match_position: number;
  winner_entity_id: number | null;
}

// ── Players ─────────────────────────────────────────────────

interface Player {
  id: string;
  name: string | null;
  isOnline: boolean;
}
```

---

## Client → Server Events

### `JOIN_SESSION`

Send immediately after the connection opens. First player to join becomes the **host**.

```json
{
  "type": "JOIN_SESSION",
  "playerId": "player-uuid",
  "name": "Alice"
}
```

### `RECONNECT_SESSION`

Rejoin after a disconnect. Restores the connection without broadcasting `PLAYER_JOINED` to others.

```json
{
  "type": "RECONNECT_SESSION",
  "playerId": "player-uuid"
}
```

### `START_SESSION` *(host only)*

Signal all players that the session is starting.

```json
{ "type": "START_SESSION" }
```

### `START_NEXT_MATCH` *(host only)*

Tell the server to broadcast the current match and open voting.

```json
{ "type": "START_NEXT_MATCH" }
```

### `VOTE`

Cast a vote for one of the two entities in the current match.

```json
{
  "type": "VOTE",
  "entityId": 42
}
```

### `HOST_CONTROL` *(host only)*

Broadcast arbitrary host state (e.g. media playback sync) to all players.

```json
{
  "type": "HOST_CONTROL",
  "state": { "isPlaying": true, "time": 12.5 }
}
```

---

## Server → Client Events

### `SESSION_STATE`

Sent to the joining/reconnecting player only. Contains the full current state.

```json
{
  "type": "SESSION_STATE",
  "session": { SessionInfo },
  "currentMatch": { Match } | null,
  "players": [ Player, ... ],
  "votes": { "playerId": entityId, ... },
  "isHost": true
}
```

### `PLAYER_JOINED`

Broadcast to everyone except the new player.

```json
{
  "type": "PLAYER_JOINED",
  "player": { "id": "abc", "name": "Alice", "isOnline": true }
}
```

### `PLAYER_LEFT`

Broadcast when a player disconnects.

```json
{
  "type": "PLAYER_LEFT",
  "playerId": "abc"
}
```

### `SESSION_STARTED`

Broadcast to all when the host starts the session.

```json
{ "type": "SESSION_STARTED" }
```

### `MATCH_STARTED`

Broadcast with the current match data.

```json
{
  "type": "MATCH_STARTED",
  "match": { Match },
  "is_bye": false
}
```

### `VOTING_STARTED`

Broadcast when voting opens for a match (not sent for byes).

```json
{
  "type": "VOTING_STARTED",
  "matchId": 5
}
```

### `MATCH_UPDATED`

Broadcast after every vote with current vote counts.

```json
{
  "type": "MATCH_UPDATED",
  "matchId": 5,
  "votes": { "42": 3, "17": 1 }
}
```

`votes` is `{ [entityId: string]: number }` — entity ID keys are stringified by JSON.

### `VOTING_ENDED`

Broadcast when all online players have voted, before the result is computed.

```json
{
  "type": "VOTING_ENDED",
  "matchId": 5
}
```

### `MATCH_FINISHED`

Broadcast after the winner is persisted. Winner = most votes; tie → entity_1 wins.

```json
{
  "type": "MATCH_FINISHED",
  "matchId": 5,
  "winner_entity_id": 42
}
```

### `ROUND_FINISHED` / `ROUND_STARTED`

Broadcast when the cursor advances to a new round.

```json
{ "type": "ROUND_FINISHED", "round": 1 }
{ "type": "ROUND_STARTED", "round": 2 }
```

### `SESSION_FINISHED`

Broadcast when no votable matches remain.

```json
{
  "type": "SESSION_FINISHED",
  "winner_entity_id": 42
}
```

### `HOST_STATE_CHANGED`

Broadcast to all when the host sends `HOST_CONTROL`.

```json
{
  "type": "HOST_STATE_CHANGED",
  "state": { "isPlaying": true, "time": 12.5 }
}
```

### `ERROR`

Sent only to the player who triggered it. **Not** broadcast.

```json
{
  "type": "ERROR",
  "code": "ALREADY_VOTED"
}
```

| Code                    | Meaning                                       |
|-------------------------|-----------------------------------------------|
| `INVALID_FIRST_MESSAGE` | First message was not JOIN/RECONNECT          |
| `MISSING_PLAYER_ID`     | `playerId` was missing                        |
| `NOT_FOUND`             | Session does not exist                        |
| `SESSION_NOT_ACTIVE`    | Session is not `in_progress`                  |
| `NO_CURRENT_MATCH`      | No match at the current cursor                |
| `INVALID_ENTITY`        | `entityId` is not in the current match        |
| `ALREADY_VOTED`         | Player already voted this match               |
| `NOT_HOST`              | Action requires host privileges               |
| `UNKNOWN_EVENT`         | Unrecognized event `type`                     |

---

## Event Flow Diagram

```
Client (Host)                Server                  Client (Player)
     |                          |                          |
     |── JOIN_SESSION ─────────►|                          |
     |◄── SESSION_STATE ───────|                          |
     |                          |◄── JOIN_SESSION ─────────|
     |◄── PLAYER_JOINED ──────|── SESSION_STATE ─────────►|
     |                          |                          |
     |── START_SESSION ────────►|                          |
     |◄── SESSION_STARTED ─────|── SESSION_STARTED ──────►|
     |◄── MATCH_STARTED ───────|── MATCH_STARTED ────────►|
     |◄── VOTING_STARTED ──────|── VOTING_STARTED ───────►|
     |                          |                          |
     |── VOTE ─────────────────►|                          |
     |◄── MATCH_UPDATED ───────|── MATCH_UPDATED ────────►|
     |                          |◄── VOTE ─────────────────|
     |◄── MATCH_UPDATED ───────|── MATCH_UPDATED ────────►|
     |◄── VOTING_ENDED ────────|── VOTING_ENDED ─────────►|
     |◄── MATCH_FINISHED ──────|── MATCH_FINISHED ───────►|
     |                          |                          |
     |── START_NEXT_MATCH ─────►|                          |
     |◄── MATCH_STARTED ───────|── MATCH_STARTED ────────►|
     |◄── VOTING_STARTED ──────|── VOTING_STARTED ───────►|
     |       ...                |       ...                |
     |◄── SESSION_FINISHED ────|── SESSION_FINISHED ─────►|
```

---

## Reference Implementation

### 1. Zustand Store

```ts
// store/session-ws.ts
import { create } from "zustand";

type ServerEvent =
  | { type: "SESSION_STATE"; session: SessionInfo; currentMatch: Match | null; players: Player[]; votes: Record<string, number>; isHost: boolean }
  | { type: "PLAYER_JOINED"; player: Player }
  | { type: "PLAYER_LEFT"; playerId: string }
  | { type: "SESSION_STARTED" }
  | { type: "MATCH_STARTED"; match: Match; is_bye: boolean }
  | { type: "VOTING_STARTED"; matchId: number }
  | { type: "MATCH_UPDATED"; matchId: number; votes: Record<string, number> }
  | { type: "VOTING_ENDED"; matchId: number }
  | { type: "MATCH_FINISHED"; matchId: number; winner_entity_id: number }
  | { type: "ROUND_FINISHED"; round: number }
  | { type: "ROUND_STARTED"; round: number }
  | { type: "SESSION_FINISHED"; winner_entity_id: number }
  | { type: "HOST_STATE_CHANGED"; state: Record<string, unknown> }
  | { type: "ERROR"; code: string };

interface SessionWsState {
  // connection
  ws: WebSocket | null;
  isConnected: boolean;

  // data
  session: SessionInfo | null;
  currentMatch: Match | null;
  players: Player[];
  votes: Record<string, number>;       // playerId → entityId
  voteCounts: Record<string, number>;   // entityId → count
  isHost: boolean;
  hostState: Record<string, unknown>;
  error: string | null;

  // meta
  isSessionStarted: boolean;
  isVotingOpen: boolean;
  isSessionFinished: boolean;
  winnerEntityId: number | null;
}

interface SessionWsActions {
  connect: (sessionId: number, playerId: string, name?: string) => void;
  reconnect: (sessionId: number, playerId: string) => void;
  disconnect: () => void;

  sendVote: (entityId: number) => void;
  startSession: () => void;
  startNextMatch: () => void;
  sendHostControl: (state: Record<string, unknown>) => void;
}

const initialState: SessionWsState = {
  ws: null,
  isConnected: false,
  session: null,
  currentMatch: null,
  players: [],
  votes: {},
  voteCounts: {},
  isHost: false,
  hostState: {},
  error: null,
  isSessionStarted: false,
  isVotingOpen: false,
  isSessionFinished: false,
  winnerEntityId: null,
};

export const useSessionWs = create<SessionWsState & SessionWsActions>(
  (set, get) => ({
    ...initialState,

    // ── Connection ────────────────────────────────────────────

    connect: (sessionId, playerId, name) => {
      const ws = new WebSocket(
        `${import.meta.env.VITE_WS_URL}/api/sessions/${sessionId}/ws`
      );

      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: "JOIN_SESSION",
          playerId,
          name: name ?? null,
        }));
        set({ ws, isConnected: true, error: null });
      };

      ws.onmessage = (event) => {
        const data: ServerEvent = JSON.parse(event.data);
        get()._handleEvent(data);
      };

      ws.onclose = () => {
        set({ ws: null, isConnected: false });
      };

      ws.onerror = () => {
        set({ error: "CONNECTION_ERROR" });
      };
    },

    reconnect: (sessionId, playerId) => {
      const ws = new WebSocket(
        `${import.meta.env.VITE_WS_URL}/api/sessions/${sessionId}/ws`
      );

      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: "RECONNECT_SESSION",
          playerId,
        }));
        set({ ws, isConnected: true, error: null });
      };

      ws.onmessage = (event) => {
        const data: ServerEvent = JSON.parse(event.data);
        get()._handleEvent(data);
      };

      ws.onclose = () => {
        set({ ws: null, isConnected: false });
      };

      ws.onerror = () => {
        set({ error: "CONNECTION_ERROR" });
      };
    },

    disconnect: () => {
      get().ws?.close();
      set(initialState);
    },

    // ── Sending ───────────────────────────────────────────────

    sendVote: (entityId) => {
      get().ws?.send(JSON.stringify({ type: "VOTE", entityId }));
    },

    startSession: () => {
      get().ws?.send(JSON.stringify({ type: "START_SESSION" }));
    },

    startNextMatch: () => {
      get().ws?.send(JSON.stringify({ type: "START_NEXT_MATCH" }));
    },

    sendHostControl: (state) => {
      get().ws?.send(JSON.stringify({ type: "HOST_CONTROL", state }));
    },

    // ── Internal event dispatcher ─────────────────────────────

    _handleEvent: (event: ServerEvent) => {
      switch (event.type) {
        case "SESSION_STATE":
          set({
            session: event.session,
            currentMatch: event.currentMatch,
            players: event.players,
            votes: event.votes,
            isHost: event.isHost,
          });
          break;

        case "PLAYER_JOINED":
          set((s) => ({ players: [...s.players, event.player] }));
          break;

        case "PLAYER_LEFT":
          set((s) => ({
            players: s.players.map((p) =>
              p.id === event.playerId ? { ...p, isOnline: false } : p
            ),
          }));
          break;

        case "SESSION_STARTED":
          set({ isSessionStarted: true });
          break;

        case "MATCH_STARTED":
          set({ currentMatch: event.match, voteCounts: {}, isVotingOpen: false });
          break;

        case "VOTING_STARTED":
          set({ isVotingOpen: true, votes: {}, voteCounts: {} });
          break;

        case "MATCH_UPDATED":
          set({ voteCounts: event.votes });
          break;

        case "VOTING_ENDED":
          set({ isVotingOpen: false });
          break;

        case "MATCH_FINISHED":
          set((s) => ({
            currentMatch: s.currentMatch
              ? { ...s.currentMatch, winner_entity_id: event.winner_entity_id, status: "FINISHED" }
              : null,
          }));
          break;

        case "ROUND_FINISHED":
          // Can trigger UI transitions (e.g. "Round 1 complete!")
          break;

        case "ROUND_STARTED":
          // Can trigger UI transitions (e.g. "Round 2 begins!")
          break;

        case "SESSION_FINISHED":
          set({
            isSessionFinished: true,
            winnerEntityId: event.winner_entity_id,
            isVotingOpen: false,
          });
          break;

        case "HOST_STATE_CHANGED":
          set({ hostState: event.state });
          break;

        case "ERROR":
          set({ error: event.code });
          break;
      }
    },
  })
);

// Expose the internal handler type without leaking it to the public interface.
declare module "./session-ws" {
  interface SessionWsActions {
    _handleEvent: (event: ServerEvent) => void;
  }
}
```

### 2. React Hook

```tsx
// hooks/use-session-socket.ts
import { useEffect, useRef } from "react";
import { useSessionWs } from "@/store/session-ws";

interface UseSessionSocketOptions {
  sessionId: number;
  playerId: string;
  name?: string;
  /** Use true when restoring a previous connection (e.g. after page refresh) */
  isReconnect?: boolean;
}

export function useSessionSocket({
  sessionId,
  playerId,
  name,
  isReconnect = false,
}: UseSessionSocketOptions) {
  const { connect, reconnect, disconnect } = useSessionWs();
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    if (isReconnect) {
      reconnect(sessionId, playerId);
    } else {
      connect(sessionId, playerId, name);
    }

    return () => {
      disconnect();
      initialized.current = false;
    };
  }, [sessionId, playerId]);
}
```

### 3. Usage in a Component

```tsx
// pages/SessionPage.tsx
import { useSessionSocket } from "@/hooks/use-session-socket";
import { useSessionWs } from "@/store/session-ws";

export function SessionPage({ sessionId }: { sessionId: number }) {
  const playerId = usePlayerId(); // your own hook / context

  // Opens the WebSocket on mount, closes on unmount.
  useSessionSocket({ sessionId, playerId, name: "Alice" });

  const {
    isConnected,
    session,
    currentMatch,
    players,
    voteCounts,
    isHost,
    isVotingOpen,
    isSessionFinished,
    winnerEntityId,
    error,
    sendVote,
    startSession,
    startNextMatch,
  } = useSessionWs();

  if (!isConnected) return <p>Connecting…</p>;
  if (error) return <p>Error: {error}</p>;

  if (isSessionFinished) {
    return <p>Winner: entity #{winnerEntityId}</p>;
  }

  return (
    <div>
      <h2>Round {session?.current_round}</h2>

      {/* Lobby: host starts when ready */}
      {isHost && !currentMatch && (
        <button onClick={startSession}>Start</button>
      )}

      {/* Current match */}
      {currentMatch && (
        <div>
          <h3>{currentMatch.entity_1?.name} vs {currentMatch.entity_2?.name}</h3>

          {isVotingOpen && (
            <>
              <button onClick={() => sendVote(currentMatch.entity_1!.id)}>
                {currentMatch.entity_1?.name}
                ({voteCounts[currentMatch.entity_1!.id] ?? 0})
              </button>
              <button onClick={() => sendVote(currentMatch.entity_2!.id)}>
                {currentMatch.entity_2?.name}
                ({voteCounts[currentMatch.entity_2!.id] ?? 0})
              </button>
            </>
          )}

          {currentMatch.status === "FINISHED" && isHost && (
            <button onClick={startNextMatch}>Next Match</button>
          )}
        </div>
      )}

      {/* Player list */}
      <ul>
        {players.map((p) => (
          <li key={p.id} style={{ opacity: p.isOnline ? 1 : 0.4 }}>
            {p.name ?? p.id}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Reconnection Strategy

The server keeps a player's info in the room after disconnect (marked offline). To reconnect:

1. Store `playerId` in `localStorage` on first join.
2. On page load, check if a `playerId` exists for this session.
3. If yes → call `reconnect(sessionId, playerId)` instead of `connect(...)`.
4. The server sends a fresh `SESSION_STATE` so the UI fully restores.

```ts
// On first join
localStorage.setItem(`session-${sessionId}-player`, playerId);

// On page load
const savedId = localStorage.getItem(`session-${sessionId}-player`);
if (savedId) {
  useSessionSocket({ sessionId, playerId: savedId, isReconnect: true });
} else {
  const newId = crypto.randomUUID();
  useSessionSocket({ sessionId, playerId: newId, name: "Alice" });
}
```

---

## Host vs Player Permissions

| Action            | Host | Player |
|-------------------|------|--------|
| `START_SESSION`   | ✓    | ✗ (ERROR: NOT_HOST) |
| `START_NEXT_MATCH`| ✓    | ✗ (ERROR: NOT_HOST) |
| `HOST_CONTROL`    | ✓    | ✗ (ERROR: NOT_HOST) |
| `VOTE`            | ✓    | ✓      |

The first player to join a session room becomes the host. Host status is returned in `SESSION_STATE.isHost`.

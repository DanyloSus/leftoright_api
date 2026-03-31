from fastapi import status


# ── helpers ──────────────────────────────────────────────────────────────────

async def _setup_tournament_with_entities(client, n: int) -> tuple[dict, list[dict]]:
    """Create a tournament owned by the authenticated client with n entities."""
    t = (await client.post("/api/tournaments/", json={"name": "T"})).json()
    entities = []
    for i in range(n):
        e = (await client.post(
            f"/api/tournaments/{t['id']}/entities/",
            json={"name": f"Entity {i}"},
        )).json()
        entities.append(e)
    return t, entities


async def _start_session(client, tournament_id: int) -> dict:
    resp = await client.post(f"/api/tournaments/{tournament_id}/sessions/")
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()


# ── start session ─────────────────────────────────────────────────────────────

async def test_start_session(auth_client):
    t, _ = await _setup_tournament_with_entities(auth_client, 4)
    resp = await auth_client.post(f"/api/tournaments/{t['id']}/sessions/")
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["tournament_id"] == t["id"]
    assert data["status"] == "in_progress"
    assert data["total_rounds"] == 2   # 4 entities → 2 rounds
    assert data["winner_entity_id"] is None
    assert data["current_match"] is not None


async def test_start_session_2_entities(auth_client):
    t, _ = await _setup_tournament_with_entities(auth_client, 2)
    data = await _start_session(auth_client, t["id"])
    assert data["total_rounds"] == 1
    match = data["current_match"]
    assert match["entity_1"] is not None
    assert match["entity_2"] is not None
    assert match["is_bye"] is False


async def test_start_session_tournament_not_found(auth_client):
    resp = await auth_client.post("/api/tournaments/9999/sessions/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_start_session_too_few_entities(auth_client):
    t, _ = await _setup_tournament_with_entities(auth_client, 1)
    resp = await auth_client.post(f"/api/tournaments/{t['id']}/sessions/")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


async def test_start_session_no_entities(auth_client):
    t = (await auth_client.post("/api/tournaments/", json={"name": "Empty"})).json()
    resp = await auth_client.post(f"/api/tournaments/{t['id']}/sessions/")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


async def test_start_session_requires_auth(client):
    resp = await client.post("/api/tournaments/1/sessions/")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ── get session ───────────────────────────────────────────────────────────────

async def test_get_session(auth_client):
    t, _ = await _setup_tournament_with_entities(auth_client, 2)
    session = await _start_session(auth_client, t["id"])
    resp = await auth_client.get(f"/api/sessions/{session['id']}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["id"] == session["id"]


async def test_get_session_not_found(auth_client):
    resp = await auth_client.get("/api/sessions/9999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_get_session_no_auth_required(client):
    """Sessions are publicly readable — no token needed."""
    r = await client.post("/api/auth/register", json={
        "email": "pub@example.com", "username": "pub", "password": "pubpassword1",
    })
    client.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    t, _ = await _setup_tournament_with_entities(client, 2)
    session = await _start_session(client, t["id"])

    del client.headers["Authorization"]
    resp = await client.get(f"/api/sessions/{session['id']}")
    assert resp.status_code == status.HTTP_200_OK


# ── vote ──────────────────────────────────────────────────────────────────────

async def test_vote_advances_session(auth_client):
    t, _ = await _setup_tournament_with_entities(auth_client, 4)
    session = await _start_session(auth_client, t["id"])
    match = session["current_match"]
    chosen = match["entity_1"]["id"]

    resp = await auth_client.post(
        f"/api/sessions/{session['id']}/vote",
        json={"chosen_entity_id": chosen},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["is_completed"] is False
    assert data["session"]["status"] == "in_progress"


async def test_vote_completes_session(auth_client):
    """2-entity bracket: single vote finishes the session."""
    t, _ = await _setup_tournament_with_entities(auth_client, 2)
    session = await _start_session(auth_client, t["id"])
    match = session["current_match"]
    chosen = match["entity_1"]["id"]

    resp = await auth_client.post(
        f"/api/sessions/{session['id']}/vote",
        json={"chosen_entity_id": chosen},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["is_completed"] is True
    assert data["session"]["status"] == "completed"
    assert data["session"]["winner_entity_id"] == chosen


async def test_vote_invalid_entity(auth_client):
    t, _ = await _setup_tournament_with_entities(auth_client, 2)
    session = await _start_session(auth_client, t["id"])
    resp = await auth_client.post(
        f"/api/sessions/{session['id']}/vote",
        json={"chosen_entity_id": 99999},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


async def test_vote_on_completed_session(auth_client):
    t, _ = await _setup_tournament_with_entities(auth_client, 2)
    session = await _start_session(auth_client, t["id"])
    chosen = session["current_match"]["entity_1"]["id"]
    await auth_client.post(
        f"/api/sessions/{session['id']}/vote",
        json={"chosen_entity_id": chosen},
    )
    # vote again on completed session
    resp = await auth_client.post(
        f"/api/sessions/{session['id']}/vote",
        json={"chosen_entity_id": chosen},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


async def test_vote_session_not_found(auth_client):
    resp = await auth_client.post(
        "/api/sessions/9999/vote",
        json={"chosen_entity_id": 1},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_vote_other_user_forbidden(client):
    """Session owned by user1 — user2 cannot vote on it."""
    r1 = await client.post("/api/auth/register", json={
        "email": "s_owner@example.com", "username": "s_owner", "password": "ownerpassword1",
    })
    client.headers["Authorization"] = f"Bearer {r1.json()['access_token']}"
    t, _ = await _setup_tournament_with_entities(client, 2)
    session = await _start_session(client, t["id"])

    r2 = await client.post("/api/auth/register", json={
        "email": "s_other@example.com", "username": "s_other", "password": "otherpassword1",
    })
    client.headers["Authorization"] = f"Bearer {r2.json()['access_token']}"

    chosen = session["current_match"]["entity_1"]["id"]
    resp = await client.post(
        f"/api/sessions/{session['id']}/vote",
        json={"chosen_entity_id": chosen},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


async def test_full_bracket_4_entities(auth_client):
    """Vote through all matches of a 4-entity bracket until completion."""
    t, _ = await _setup_tournament_with_entities(auth_client, 4)
    session = await _start_session(auth_client, t["id"])
    session_id = session["id"]

    # Keep voting for entity_1 of each current match until done
    for _ in range(10):  # safety cap
        state = (await auth_client.get(f"/api/sessions/{session_id}")).json()
        if state["status"] == "completed":
            break
        match = state["current_match"]
        chosen = match["entity_1"]["id"]
        result = (await auth_client.post(
            f"/api/sessions/{session_id}/vote",
            json={"chosen_entity_id": chosen},
        )).json()
        if result["is_completed"]:
            break

    final = (await auth_client.get(f"/api/sessions/{session_id}")).json()
    assert final["status"] == "completed"
    assert final["winner_entity_id"] is not None

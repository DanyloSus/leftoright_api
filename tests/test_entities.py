from fastapi import status


# ── helpers ──────────────────────────────────────────────────────────────────


async def _create_tournament(client, name="T") -> dict:
    resp = await client.post("/api/tournaments/", json={"name": name})
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()


async def _create_entity(client, tournament_id: int, name="Entity A") -> dict:
    resp = await client.post(
        f"/api/tournaments/{tournament_id}/entities/",
        json={"name": name},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()


# ── create ────────────────────────────────────────────────────────────────────


async def test_create_entity(auth_client):
    t = await _create_tournament(auth_client)
    resp = await auth_client.post(
        f"/api/tournaments/{t['id']}/entities/",
        json={"name": "Song A", "youtube_url": "https://youtube.com/watch?v=abc"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["name"] == "Song A"
    assert data["youtube_url"] == "https://youtube.com/watch?v=abc"
    assert data["tournament_id"] == t["id"]
    assert "id" in data


async def test_create_entity_without_youtube_url(auth_client):
    t = await _create_tournament(auth_client)
    resp = await auth_client.post(
        f"/api/tournaments/{t['id']}/entities/",
        json={"name": "Song B"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["youtube_url"] is None


async def test_create_entity_requires_auth(client):
    resp = await client.post("/api/tournaments/1/entities/", json={"name": "X"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_entity_tournament_not_found(auth_client):
    resp = await auth_client.post("/api/tournaments/9999/entities/", json={"name": "X"})
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_create_entity_other_user_forbidden(client):
    r1 = await client.post(
        "/api/auth/register",
        json={
            "email": "owner_e@example.com",
            "username": "owner_e",
            "password": "ownerpassword1",
        },
    )
    token1 = r1.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token1}"
    t = (await client.post("/api/tournaments/", json={"name": "Private"})).json()

    r2 = await client.post(
        "/api/auth/register",
        json={
            "email": "other_e@example.com",
            "username": "other_e",
            "password": "otherpassword1",
        },
    )
    client.headers["Authorization"] = f"Bearer {r2.json()['access_token']}"

    resp = await client.post(
        f"/api/tournaments/{t['id']}/entities/", json={"name": "Stolen"}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


# ── list ──────────────────────────────────────────────────────────────────────


async def test_list_entities(auth_client):
    t = await _create_tournament(auth_client)
    await _create_entity(auth_client, t["id"], "A")
    await _create_entity(auth_client, t["id"], "B")
    resp = await auth_client.get(f"/api/tournaments/{t['id']}/entities/")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()) == 2


async def test_list_entities_empty(auth_client):
    t = await _create_tournament(auth_client)
    resp = await auth_client.get(f"/api/tournaments/{t['id']}/entities/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []


async def test_list_entities_tournament_not_found(auth_client):
    resp = await auth_client.get("/api/tournaments/9999/entities/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


# ── delete ────────────────────────────────────────────────────────────────────


async def test_delete_entity(auth_client):
    t = await _create_tournament(auth_client)
    e = await _create_entity(auth_client, t["id"])
    resp = await auth_client.delete(f"/api/tournaments/{t['id']}/entities/{e['id']}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT
    entities = (await auth_client.get(f"/api/tournaments/{t['id']}/entities/")).json()
    assert all(x["id"] != e["id"] for x in entities)


async def test_delete_entity_not_found(auth_client):
    t = await _create_tournament(auth_client)
    resp = await auth_client.delete(f"/api/tournaments/{t['id']}/entities/9999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_entity_other_user_forbidden(client):
    r1 = await client.post(
        "/api/auth/register",
        json={
            "email": "del_owner_e@example.com",
            "username": "del_owner_e",
            "password": "ownerpassword1",
        },
    )
    token1 = r1.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token1}"
    t = (await client.post("/api/tournaments/", json={"name": "T"})).json()
    e = (
        await client.post(f"/api/tournaments/{t['id']}/entities/", json={"name": "E"})
    ).json()

    r2 = await client.post(
        "/api/auth/register",
        json={
            "email": "del_other_e@example.com",
            "username": "del_other_e",
            "password": "otherpassword1",
        },
    )
    client.headers["Authorization"] = f"Bearer {r2.json()['access_token']}"

    resp = await client.delete(f"/api/tournaments/{t['id']}/entities/{e['id']}")
    assert resp.status_code == status.HTTP_403_FORBIDDEN

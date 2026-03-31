from fastapi import status


async def test_create_tournament(auth_client):
    resp = await auth_client.post("/api/tournaments/", json={"name": "My Tournament"})
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["name"] == "My Tournament"
    assert data["description"] is None
    assert "id" in data
    assert "user_id" in data


async def test_create_tournament_with_description(auth_client):
    resp = await auth_client.post("/api/tournaments/", json={
        "name": "My Tournament",
        "description": "A fun tournament",
    })
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["description"] == "A fun tournament"


async def test_list_tournaments(auth_client):
    await auth_client.post("/api/tournaments/", json={"name": "T1"})
    await auth_client.post("/api/tournaments/", json={"name": "T2"})
    resp = await auth_client.get("/api/tournaments/")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()) == 2


async def test_list_tournaments_requires_auth(client):
    resp = await client.get("/api/tournaments/")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_tournament(auth_client):
    created = (await auth_client.post("/api/tournaments/", json={"name": "T"})).json()
    resp = await auth_client.get(f"/api/tournaments/{created['id']}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["id"] == created["id"]


async def test_get_tournament_not_found(auth_client):
    resp = await auth_client.get("/api/tournaments/9999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_update_tournament(auth_client):
    created = (await auth_client.post("/api/tournaments/", json={"name": "Old Name"})).json()
    resp = await auth_client.patch(f"/api/tournaments/{created['id']}", json={"name": "New Name"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["name"] == "New Name"


async def test_delete_tournament(auth_client):
    created = (await auth_client.post("/api/tournaments/", json={"name": "To Delete"})).json()
    resp = await auth_client.delete(f"/api/tournaments/{created['id']}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT
    resp = await auth_client.get(f"/api/tournaments/{created['id']}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_other_user_cannot_update_tournament(client):
    # Register first user and create a tournament
    r1 = await client.post("/api/auth/register", json={
        "email": "owner@example.com", "username": "owner", "password": "ownerpassword1",
    })
    token1 = r1.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token1}"
    created = (await client.post("/api/tournaments/", json={"name": "Private"})).json()

    # Register second user
    r2 = await client.post("/api/auth/register", json={
        "email": "other@example.com", "username": "other", "password": "otherpassword1",
    })
    token2 = r2.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token2}"

    resp = await client.patch(f"/api/tournaments/{created['id']}", json={"name": "Hijacked"})
    assert resp.status_code == status.HTTP_403_FORBIDDEN


async def test_other_user_cannot_delete_tournament(client):
    r1 = await client.post("/api/auth/register", json={
        "email": "del_owner@example.com", "username": "del_owner", "password": "ownerpassword1",
    })
    token1 = r1.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token1}"
    created = (await client.post("/api/tournaments/", json={"name": "Private"})).json()

    r2 = await client.post("/api/auth/register", json={
        "email": "del_other@example.com", "username": "del_other", "password": "otherpassword1",
    })
    token2 = r2.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token2}"

    resp = await client.delete(f"/api/tournaments/{created['id']}")
    assert resp.status_code == status.HTTP_403_FORBIDDEN

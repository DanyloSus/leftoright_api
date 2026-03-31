from fastapi import status


async def test_create_user(client):
    resp = await client.post("/api/users/", json={"email": "alice@example.com", "username": "alice"})
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert "id" in data


async def test_list_users(client):
    await client.post("/api/users/", json={"email": "a@example.com", "username": "a"})
    await client.post("/api/users/", json={"email": "b@example.com", "username": "b"})
    resp = await client.get("/api/users/")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()) == 2


async def test_get_user_by_id(client):
    created = (await client.post("/api/users/", json={"email": "c@example.com", "username": "c"})).json()
    resp = await client.get(f"/api/users/{created['id']}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["id"] == created["id"]


async def test_get_user_not_found(client):
    resp = await client.get("/api/users/9999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_update_user(client):
    created = (await client.post("/api/users/", json={"email": "d@example.com", "username": "d"})).json()
    resp = await client.patch(f"/api/users/{created['id']}", json={"username": "updated"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["username"] == "updated"


async def test_delete_user(client):
    created = (await client.post("/api/users/", json={"email": "e@example.com", "username": "e"})).json()
    resp = await client.delete(f"/api/users/{created['id']}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT
    resp = await client.get(f"/api/users/{created['id']}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND

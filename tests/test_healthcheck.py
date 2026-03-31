from fastapi import status


async def test_healthcheck(client):
    resp = await client.get("/api/healthcheck/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"msg": "OK"}

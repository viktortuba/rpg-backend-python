import pytest
from jose import jwt
from app.config import settings

pytestmark = pytest.mark.asyncio


async def test_register_success(client):
    resp = await client.post("/api/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["role"] == "User"
    assert "id" in data
    assert "password" not in data


async def test_register_game_master(client):
    resp = await client.post("/api/register", json={
        "username": "gm1",
        "email": "gm1@example.com",
        "password": "secret123",
        "role": "GameMaster",
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "GameMaster"


async def test_register_duplicate_username(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "pw"}
    await client.post("/api/register", json=payload)
    resp = await client.post("/api/register", json={**payload, "email": "bob2@example.com"})
    assert resp.status_code == 400
    assert "Username" in resp.json()["detail"]


async def test_register_duplicate_email(client):
    await client.post("/api/register", json={"username": "carol", "email": "carol@example.com", "password": "pw"})
    resp = await client.post("/api/register", json={"username": "carol2", "email": "carol@example.com", "password": "pw"})
    assert resp.status_code == 400
    assert "Email" in resp.json()["detail"]


async def test_login_success(client):
    await client.post("/api/register", json={
        "username": "dave",
        "email": "dave@example.com",
        "password": "hunter2",
    })
    resp = await client.post("/api/login", json={"username": "dave", "password": "hunter2"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    decoded = jwt.decode(data["access_token"], settings.JWT_SECRET, algorithms=["HS256"])
    assert decoded["username"] == "dave"
    assert decoded["role"] == "User"
    assert "sub" in decoded


async def test_login_wrong_password(client):
    await client.post("/api/register", json={
        "username": "eve",
        "email": "eve@example.com",
        "password": "correct",
    })
    resp = await client.post("/api/login", json={"username": "eve", "password": "wrong"})
    assert resp.status_code == 401


async def test_login_unknown_user(client):
    resp = await client.post("/api/login", json={"username": "nobody", "password": "pw"})
    assert resp.status_code == 401


async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "account"

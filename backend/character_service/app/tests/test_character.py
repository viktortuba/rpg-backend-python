import pytest
from app.tests.conftest import make_token

pytestmark = pytest.mark.asyncio


async def test_list_characters_game_master(client, seeded_class):
    ac, redis, db = client
    token, uid = make_token(role="GameMaster")
    resp = await ac.get("/api/character", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_characters_user_forbidden(client):
    ac, redis, db = client
    token, _ = make_token(role="User")
    resp = await ac.get("/api/character", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_create_character(client, seeded_class):
    ac, redis, db = client
    token, uid = make_token(role="User")
    resp = await ac.post("/api/character", json={
        "name": "Thorin",
        "health": 100,
        "mana": 50,
        "base_strength": 10,
        "base_agility": 5,
        "base_intelligence": 3,
        "base_faith": 2,
        "class_id": seeded_class.id,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Thorin"
    assert data["created_by"] == uid
    assert data["effective_stats"]["strength"] == 10
    assert data["effective_stats"]["agility"] == 5


async def test_create_character_duplicate_name(client, seeded_class):
    ac, redis, db = client
    token, uid = make_token(role="User")
    payload = {"name": "Hero", "health": 100, "mana": 50, "class_id": seeded_class.id}
    await ac.post("/api/character", json=payload, headers={"Authorization": f"Bearer {token}"})
    resp = await ac.post("/api/character", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


async def test_get_character_owner_can_access(client, seeded_class):
    ac, redis, db = client
    token, uid = make_token(role="User")
    create_resp = await ac.post("/api/character", json={
        "name": "Legolas",
        "health": 80,
        "mana": 60,
        "class_id": seeded_class.id,
    }, headers={"Authorization": f"Bearer {token}"})
    char_id = create_resp.json()["id"]

    resp = await ac.get(f"/api/character/{char_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Legolas"


async def test_get_character_other_user_forbidden(client, seeded_class):
    ac, redis, db = client
    owner_token, _ = make_token(role="User")
    create_resp = await ac.post("/api/character", json={
        "name": "Gimli",
        "health": 90,
        "mana": 20,
        "class_id": seeded_class.id,
    }, headers={"Authorization": f"Bearer {owner_token}"})
    char_id = create_resp.json()["id"]

    other_token, _ = make_token(role="User")
    resp = await ac.get(f"/api/character/{char_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403


async def test_get_character_game_master_can_access_any(client, seeded_class):
    ac, redis, db = client
    user_token, _ = make_token(role="User")
    create_resp = await ac.post("/api/character", json={
        "name": "Aragorn",
        "health": 110,
        "mana": 40,
        "class_id": seeded_class.id,
    }, headers={"Authorization": f"Bearer {user_token}"})
    char_id = create_resp.json()["id"]

    gm_token, _ = make_token(role="GameMaster")
    resp = await ac.get(f"/api/character/{char_id}", headers={"Authorization": f"Bearer {gm_token}"})
    assert resp.status_code == 200


async def test_get_character_cache_hit(client, seeded_class):
    ac, redis, db = client
    import json
    token, uid = make_token(role="User")
    create_resp = await ac.post("/api/character", json={
        "name": "Gandalf",
        "health": 100,
        "mana": 100,
        "class_id": seeded_class.id,
    }, headers={"Authorization": f"Bearer {token}"})
    char_id = create_resp.json()["id"]

    # Simulate cache hit with serialized data
    cached_data = create_resp.json()
    cached_data["effective_stats"] = {"strength": 0, "agility": 0, "intelligence": 0, "faith": 0}
    cached_data["items"] = []
    redis.get = AsyncMock(return_value=json.dumps(cached_data))

    resp = await ac.get(f"/api/character/{char_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    # Verify cache was checked
    redis.get.assert_called_once_with(f"character:{char_id}")

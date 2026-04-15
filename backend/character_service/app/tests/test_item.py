import pytest
from app.tests.conftest import make_token

pytestmark = pytest.mark.asyncio


async def _create_character(ac, seeded_class, name, token):
    resp = await ac.post("/api/character", json={
        "name": name,
        "health": 100,
        "mana": 50,
        "class_id": seeded_class.id,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_create_item(client):
    ac, redis, db = client
    token, _ = make_token(role="User")
    resp = await ac.post("/api/items", json={
        "base_name": "Sword",
        "bonus_strength": 5,
        "bonus_agility": 2,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Sword of Strength"
    assert data["bonus_strength"] == 5


async def test_item_name_suffix_agility(client):
    ac, redis, db = client
    token, _ = make_token(role="User")
    resp = await ac.post("/api/items", json={
        "base_name": "Dagger",
        "bonus_strength": 1,
        "bonus_agility": 10,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["name"] == "Dagger of Agility"


async def test_item_name_suffix_intelligence(client):
    ac, redis, db = client
    token, _ = make_token(role="User")
    resp = await ac.post("/api/items", json={
        "base_name": "Staff",
        "bonus_intelligence": 8,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["name"] == "Staff of Intelligence"


async def test_item_name_no_suffix_when_all_zero(client):
    ac, redis, db = client
    token, _ = make_token(role="User")
    resp = await ac.post("/api/items", json={"base_name": "Rock"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["name"] == "Rock"


async def test_list_items_game_master_only(client):
    ac, redis, db = client
    gm_token, _ = make_token(role="GameMaster")
    user_token, _ = make_token(role="User")

    resp = await ac.get("/api/items", headers={"Authorization": f"Bearer {gm_token}"})
    assert resp.status_code == 200

    resp = await ac.get("/api/items", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


async def test_grant_item(client, seeded_class):
    ac, redis, db = client
    token, uid = make_token(role="User")
    char_id = await _create_character(ac, seeded_class, "Knight", token)

    item_resp = await ac.post("/api/items", json={"base_name": "Shield", "bonus_faith": 3},
                              headers={"Authorization": f"Bearer {token}"})
    item_id = item_resp.json()["id"]

    resp = await ac.post("/api/items/grant", json={"character_id": char_id, "item_id": item_id},
                         headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    redis.delete.assert_called_with(f"character:{char_id}")


async def test_gift_item(client, seeded_class):
    ac, redis, db = client
    token1, _ = make_token(role="User")
    token2, _ = make_token(role="User")

    char1_id = await _create_character(ac, seeded_class, "Paladin", token1)
    char2_id = await _create_character(ac, seeded_class, "Bard", token2)

    item_resp = await ac.post("/api/items", json={"base_name": "Lute", "bonus_faith": 4},
                              headers={"Authorization": f"Bearer {token1}"})
    item_id = item_resp.json()["id"]

    # Grant item to char1
    await ac.post("/api/items/grant", json={"character_id": char1_id, "item_id": item_id},
                  headers={"Authorization": f"Bearer {token1}"})

    # Gift from char1 to char2
    resp = await ac.post("/api/items/gift", json={
        "from_character_id": char1_id,
        "to_character_id": char2_id,
        "item_id": item_id,
    }, headers={"Authorization": f"Bearer {token1}"})
    assert resp.status_code == 200

    # Both caches invalidated
    deleted_keys = [call.args[0] for call in redis.delete.call_args_list]
    assert f"character:{char1_id}" in deleted_keys
    assert f"character:{char2_id}" in deleted_keys


async def test_gift_item_not_owned(client, seeded_class):
    ac, redis, db = client
    token1, _ = make_token(role="User")
    token2, _ = make_token(role="User")

    char1_id = await _create_character(ac, seeded_class, "Druid", token1)
    char2_id = await _create_character(ac, seeded_class, "Monk", token2)

    item_resp = await ac.post("/api/items", json={"base_name": "Staff", "bonus_intelligence": 5},
                              headers={"Authorization": f"Bearer {token1}"})
    item_id = item_resp.json()["id"]

    # char1 does not own the item — gift should fail
    resp = await ac.post("/api/items/gift", json={
        "from_character_id": char1_id,
        "to_character_id": char2_id,
        "item_id": item_id,
    }, headers={"Authorization": f"Bearer {token1}"})
    assert resp.status_code == 404

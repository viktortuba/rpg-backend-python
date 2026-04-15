import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from app.tests.conftest import make_token, make_character_data

pytestmark = pytest.mark.asyncio


async def _create_duel(ac, mock_client, token, challenger_owner_id, defender_owner_id=None):
    if defender_owner_id is None:
        defender_owner_id = str(uuid.uuid4())
    challenger = make_character_data(challenger_owner_id, name="Challenger")
    defender = make_character_data(defender_owner_id, name="Defender")

    mock_client.get_character = AsyncMock(side_effect=[challenger, defender])

    resp = await ac.post("/api/challenge", json={
        "challenger_id": challenger["id"],
        "defender_id": defender["id"],
    }, headers={"Authorization": f"Bearer {token}"})

    return resp, challenger, defender


async def test_create_challenge(client):
    ac, mock_client, db = client
    token, uid = make_token(role="User")

    resp, challenger, defender = await _create_duel(ac, mock_client, token, uid)

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert data["challenger_id"] == challenger["id"]
    assert data["defender_id"] == defender["id"]


async def test_challenge_non_owner_forbidden(client):
    ac, mock_client, db = client
    token, uid = make_token(role="User")
    other_uid = str(uuid.uuid4())

    # Challenger owned by different user
    challenger = make_character_data(other_uid, name="NotMine")
    defender = make_character_data(uid, name="Mine")
    mock_client.get_character = AsyncMock(side_effect=[challenger, defender])

    resp = await ac.post("/api/challenge", json={
        "challenger_id": challenger["id"],
        "defender_id": defender["id"],
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_attack_action(client):
    ac, mock_client, db = client
    token, uid = make_token(role="User")
    resp, challenger, defender = await _create_duel(ac, mock_client, token, uid)
    duel_id = resp.json()["id"]

    attack_resp = await ac.post(f"/api/{duel_id}/attack", headers={"Authorization": f"Bearer {token}"})
    assert attack_resp.status_code == 200
    data = attack_resp.json()
    assert data["action_type"] == "attack"
    # damage = strength(10) + agility(5) = 15
    assert data["value"] == 15


async def test_cast_action(client):
    ac, mock_client, db = client
    token, uid = make_token(role="User")
    resp, challenger, _ = await _create_duel(ac, mock_client, token, uid)
    duel_id = resp.json()["id"]

    cast_resp = await ac.post(f"/api/{duel_id}/cast", headers={"Authorization": f"Bearer {token}"})
    assert cast_resp.status_code == 200
    data = cast_resp.json()
    assert data["action_type"] == "cast"
    # damage = 2 * intelligence(8) = 16
    assert data["value"] == 16


async def test_heal_action(client):
    ac, mock_client, db = client
    token, uid = make_token(role="User")
    resp, challenger, _ = await _create_duel(ac, mock_client, token, uid)
    duel_id = resp.json()["id"]

    heal_resp = await ac.post(f"/api/{duel_id}/heal", headers={"Authorization": f"Bearer {token}"})
    assert heal_resp.status_code == 200
    data = heal_resp.json()
    assert data["action_type"] == "heal"
    # heal = faith(3)
    assert data["value"] == 3


async def test_attack_cooldown(client):
    ac, mock_client, db = client
    token, uid = make_token(role="User")
    resp, _, _ = await _create_duel(ac, mock_client, token, uid)
    duel_id = resp.json()["id"]

    # First attack succeeds
    r1 = await ac.post(f"/api/{duel_id}/attack", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200

    # Immediate second attack hits cooldown
    r2 = await ac.post(f"/api/{duel_id}/attack", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 429


async def test_duel_ends_on_kill_and_item_transferred(client):
    ac, mock_client, db = client
    token, uid = make_token(role="User")

    # Set defender health very low so one attack kills them
    challenger = make_character_data(uid, name="Killer", strength=1000, agility=0)
    defender = make_character_data(str(uuid.uuid4()), name="Victim", health=1)
    mock_client.get_character = AsyncMock(side_effect=[challenger, defender, defender])
    mock_client.pick_random_item = AsyncMock(return_value=str(uuid.uuid4()))

    resp = await ac.post("/api/challenge", json={
        "challenger_id": challenger["id"],
        "defender_id": defender["id"],
    }, headers={"Authorization": f"Bearer {token}"})
    duel_id = resp.json()["id"]

    attack_resp = await ac.post(f"/api/{duel_id}/attack", headers={"Authorization": f"Bearer {token}"})
    assert attack_resp.status_code == 200
    assert "wins" in attack_resp.json()["message"]

    # Item transfer should have been attempted
    mock_client.gift_item.assert_called_once()

    # Duel should now be finished
    duel_resp = await ac.get(f"/api/{duel_id}", headers={"Authorization": f"Bearer {token}"})
    assert duel_resp.json()["status"] == "finished"


async def test_non_participant_cannot_act(client):
    ac, mock_client, db = client
    token, uid = make_token(role="User")
    resp, _, _ = await _create_duel(ac, mock_client, token, uid)
    duel_id = resp.json()["id"]

    stranger_token, _ = make_token(role="User")
    r = await ac.post(f"/api/{duel_id}/attack", headers={"Authorization": f"Bearer {stranger_token}"})
    assert r.status_code == 403


async def test_health_endpoint(client):
    ac, _, _ = client
    resp = await ac.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "combat"

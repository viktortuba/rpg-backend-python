import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.character_snapshot import CharacterSnapshot
from app.models.duel import Duel, DuelAction
from app.schemas.duel import ChallengeRequest, ActionResponse, DuelRead
from app.config import settings

logger = logging.getLogger(__name__)

COOLDOWNS = {
    "attack": 1,
    "cast": 2,
    "heal": 2,
}


def _get_now() -> datetime:
    """Injectable clock for testing."""
    return datetime.now(timezone.utc)


def _compute_action_value(action_type: str, snapshot: CharacterSnapshot) -> int:
    if action_type == "attack":
        return snapshot.eff_strength + snapshot.eff_agility
    elif action_type == "cast":
        return 2 * snapshot.eff_intelligence
    elif action_type == "heal":
        return snapshot.eff_faith
    raise ValueError(f"Unknown action type: {action_type}")


async def _load_duel(duel_id: str, db: AsyncSession) -> Duel:
    result = await db.execute(
        select(Duel)
        .where(Duel.id == duel_id)
        .options(
            selectinload(Duel.challenger),
            selectinload(Duel.defender),
            selectinload(Duel.actions),
        )
    )
    duel = result.scalar_one_or_none()
    if not duel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duel not found")
    return duel


async def create_challenge(
    data: ChallengeRequest,
    challenger_data: dict,
    defender_data: dict,
    current_user_id: str,
    db: AsyncSession,
) -> DuelRead:
    # Validate challenger ownership
    if challenger_data["created_by"] != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own the challenger character")

    def _make_snapshot(char: dict) -> CharacterSnapshot:
        eff = char.get("effective_stats", {})
        return CharacterSnapshot(
            id=char["id"],
            name=char["name"],
            current_health=char["health"],
            mana=char["mana"],
            eff_strength=eff.get("strength", 0),
            eff_agility=eff.get("agility", 0),
            eff_intelligence=eff.get("intelligence", 0),
            eff_faith=eff.get("faith", 0),
            owner_id=char["created_by"],
        )

    challenger_snap = _make_snapshot(challenger_data)
    defender_snap = _make_snapshot(defender_data)

    # Upsert snapshots (use merge to handle re-challenges)
    challenger_snap = await db.merge(challenger_snap)
    defender_snap = await db.merge(defender_snap)

    # Reset health to full for the new duel
    challenger_snap.current_health = challenger_data["health"]
    defender_snap.current_health = defender_data["health"]

    duel = Duel(
        challenger_id=challenger_snap.id,
        defender_id=defender_snap.id,
        status="active",
    )
    db.add(duel)
    await db.commit()
    await db.refresh(duel)
    logger.info("Duel %s created: %s vs %s", duel.id, challenger_snap.name, defender_snap.name)
    return DuelRead.model_validate(duel)


async def perform_action(
    duel_id: str,
    action_type: str,
    current_user_id: str,
    db: AsyncSession,
    character_client,
    token: str,
    now_fn=_get_now,
) -> ActionResponse:
    duel = await _load_duel(duel_id, db)

    if duel.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duel is not active")

    now = now_fn()

    # Check timeout (draw after 5 minutes)
    if (now - duel.started_at.replace(tzinfo=timezone.utc)).total_seconds() > settings.DUEL_TIMEOUT_SECONDS:
        duel.status = "draw"
        duel.finished_at = now
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duel ended in a draw (timeout)")

    # Identify actor and target
    challenger = duel.challenger
    defender = duel.defender

    if challenger.owner_id == current_user_id:
        actor = challenger
        target = defender
    elif defender.owner_id == current_user_id:
        actor = defender
        target = challenger
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a participant in this duel")

    # Enforce cooldown
    cooldown_secs = COOLDOWNS[action_type]
    last_action = next(
        (a for a in sorted(duel.actions, key=lambda x: x.executed_at, reverse=True)
         if a.character_id == actor.id and a.action_type == action_type),
        None,
    )
    if last_action:
        elapsed = (now - last_action.executed_at.replace(tzinfo=timezone.utc)).total_seconds()
        if elapsed < cooldown_secs:
            remaining = cooldown_secs - elapsed
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Action on cooldown. Try again in {remaining:.1f}s",
            )

    value = _compute_action_value(action_type, actor)

    if action_type == "heal":
        actor.current_health += value
        message = f"{actor.name} healed for {value} HP"
    else:
        target.current_health = max(0, target.current_health - value)
        message = f"{actor.name} dealt {value} damage to {target.name}"

    action = DuelAction(
        duel_id=duel.id,
        character_id=actor.id,
        action_type=action_type,
        executed_at=now,
        value=value,
    )
    db.add(action)

    # Check win condition
    if target.current_health <= 0:
        duel.status = "finished"
        duel.winner_id = actor.id
        duel.finished_at = now
        message += f". {target.name} has been defeated! {actor.name} wins!"
        await db.commit()

        # Transfer random item from loser to winner
        try:
            loser_data = await character_client.get_character(target.id, token)
            item_id = await character_client.pick_random_item(loser_data)
            if item_id:
                await character_client.gift_item(target.id, actor.id, item_id, token)
                logger.info("Item %s transferred from %s to %s", item_id, target.id, actor.id)
        except Exception as exc:
            logger.error("Failed to transfer item after duel: %s", exc)
    else:
        await db.commit()

    return ActionResponse(duel_id=duel_id, action_type=action_type, value=value, message=message)


async def get_duel(duel_id: str, db: AsyncSession) -> DuelRead:
    duel = await _load_duel(duel_id, db)
    return DuelRead.model_validate(duel)

import logging
import random
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings

logger = logging.getLogger(__name__)


class CharacterClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.CHARACTER_SERVICE_URL,
            timeout=10.0,
        )

    async def get_character(self, character_id: str, token: str) -> dict:
        resp = await self._client.get(
            f"/api/character/{character_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def gift_item(self, from_character_id: str, to_character_id: str, item_id: str, token: str) -> None:
        logger.info("Transferring item %s from %s to %s", item_id, from_character_id, to_character_id)
        resp = await self._client.post(
            "/api/items/gift",
            json={
                "from_character_id": from_character_id,
                "to_character_id": to_character_id,
                "item_id": item_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()

    async def pick_random_item(self, character_data: dict) -> str | None:
        items = character_data.get("items", [])
        if not items:
            return None
        return random.choice(items)["id"]

    async def aclose(self):
        await self._client.aclose()


character_client = CharacterClient()

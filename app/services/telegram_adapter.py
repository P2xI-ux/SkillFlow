import httpx

from app.core.config import settings


class TelegramAdapter:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip("/")
        self.bot_token = settings.telegram_bot_token

    def _get_headers(self, telegram_id: str | None = None) -> dict:
        headers = {"X-Bot-Token": self.bot_token}
        if telegram_id:
            headers["X-Telegram-Id"] = str(telegram_id)
        return headers

    async def fetch_tests(self, telegram_id: str | None = None):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.api_base_url}/api/tests", headers=self._get_headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()

    async def fetch_stats(self, telegram_id: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.api_base_url}/api/stats/me",
                headers=self._get_headers(telegram_id),
            )
            response.raise_for_status()
            return response.json()

    async def fetch_rating(self, subject_id: int | None = None):
        params = {"subject_id": subject_id} if subject_id else None
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.api_base_url}/api/ratings",
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def fetch_test_detail(self, test_id: int, telegram_id: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.api_base_url}/api/tests/{test_id}",
                headers=self._get_headers(telegram_id),
            )
            response.raise_for_status()
            return response.json()

    async def submit_attempt(
        self, test_id: int, telegram_id: str, answers: list, allow_retake: bool = False
    ):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.api_base_url}/api/tests/{test_id}/attempt",
                json={"answers": answers, "allow_retake": allow_retake},
                headers=self._get_headers(telegram_id),
            )
            response.raise_for_status()
            return response.json()

    async def connect_account(self, code: str, telegram_id: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.api_base_url}/api/telegram/connect",
                json={"code": code, "telegram_id": telegram_id},
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

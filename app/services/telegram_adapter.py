import httpx


class TelegramAdapter:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip("/")

    async def fetch_tests(self):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.api_base_url}/api/tests")
            response.raise_for_status()
            return response.json()

    async def fetch_stats(self, token: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.api_base_url}/api/stats/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def fetch_rating(self, subject_id: int | None = None):
        params = {"subject_id": subject_id} if subject_id else None
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.api_base_url}/api/ratings", params=params)
            response.raise_for_status()
            return response.json()

    async def connect_account(self, code: str, telegram_id: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.api_base_url}/api/telegram/connect",
                json={"code": code, "telegram_id": telegram_id},
            )
            response.raise_for_status()
            return response.json()

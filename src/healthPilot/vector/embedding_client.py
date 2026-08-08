import httpx

from healthPilot.core.config import get_settings
from healthPilot.core.exceptions import SyncError


class EmbeddingClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def embed_text(self, text: str) -> list[float]:
        url = f"{self.settings.OPENAI_BASE_URL.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.EMBEDDING_MODEL,
            "input": text,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise SyncError(
                f"Embedding API error ({response.status_code}): {response.text}",
                code="EMBEDDING_API_ERROR",
            )

        data = response.json()
        try:
            return data["data"][0]["embedding"]
        except (KeyError, IndexError, TypeError) as exc:
            raise SyncError("Invalid embedding API response", code="EMBEDDING_PARSE_ERROR") from exc

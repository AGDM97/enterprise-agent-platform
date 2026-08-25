import os

import httpx


class OllamaEmbeddingProvider:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11435",
            )
        ).rstrip("/")

        self.model = model or os.getenv(
            "OLLAMA_EMBEDDING_MODEL",
            "all-minilm",
        )

        self.timeout = timeout

    async def embed(
        self,
        text: str,
    ) -> list[float]:
        payload = {
            "model": self.model,
            "input": text,
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json=payload,
            )

            response.raise_for_status()

        body = response.json()

        embeddings = body.get(
            "embeddings",
            [],
        )

        if not embeddings:
            raise ValueError(
                "The embedding provider returned "
                "no vectors."
            )

        return embeddings[0]
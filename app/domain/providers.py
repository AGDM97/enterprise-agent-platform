from abc import ABC, abstractmethod

from app.domain.models import (
    ChatRequest,
    ChatResponse,
    Document,
)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        raise NotImplementedError

    @abstractmethod
    async def generate_with_context(
        self,
        request: ChatRequest,
        documents: list[Document],
    ) -> ChatResponse:
        raise NotImplementedError
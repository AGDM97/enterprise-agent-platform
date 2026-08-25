from abc import ABC, abstractmethod

from app.domain.models import Document, UserContext


class DocumentRetriever(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        user: UserContext,
    ) -> list[Document]:
        raise NotImplementedError
import os

from uuid import NAMESPACE_URL, uuid5

from qdrant_client import AsyncQdrantClient

from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    IsEmptyCondition,
    MatchAny,
    MatchValue,
    PayloadField,
    PointStruct,
    VectorParams,
)

from app.domain.models import (
    Document,
    UserContext,
)

from app.domain.retrieval import (
    DocumentRetriever,
)

from app.infrastructure.ollama_embeddings import (
    OllamaEmbeddingProvider,
)


class QdrantDocumentRetriever(
    DocumentRetriever
):
    def __init__(
        self,
        url: str | None = None,
        collection_name: str | None = None,
        vector_size: int = 384,
        limit: int = 3,
    ) -> None:
        self.url = url or os.getenv(
            "QDRANT_URL",
            "http://localhost:6333",
        )

        self.collection_name = (
            collection_name
            or os.getenv(
                "QDRANT_COLLECTION",
                "enterprise_agent_documents",
            )
        )

        self.vector_size = vector_size

        self.limit = limit

        self.client = AsyncQdrantClient(
            url=self.url,
        )

        self.embedding_provider = (
            OllamaEmbeddingProvider()
        )

    async def ensure_collection(
        self,
    ) -> None:
        exists = await self.client.collection_exists(
            collection_name=self.collection_name,
        )

        if exists:
            return

        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE,
            ),
        )

    async def index_documents(
        self,
        documents: list[Document],
    ) -> int:
        await self.ensure_collection()

        points = []

        for document in documents:
            text = (
                f"{document.title}\n"
                f"{document.content}"
            )

            vector = await self.embedding_provider.embed(
                text
            )

            point_id = str(
                uuid5(
                    NAMESPACE_URL,
                    (
                        f"{document.tenant_id}:"
                        f"{document.document_id}"
                    ),
                )
            )

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=document.model_dump(),
                )
            )

        if not points:
            return 0

        await self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

        return len(points)

    async def search(
        self,
        query: str,
        user: UserContext,
    ) -> list[Document]:
        query_vector = (
            await self.embedding_provider.embed(
                query
            )
        )

        access_conditions = [
            IsEmptyCondition(
                is_empty=PayloadField(
                    key="allowed_groups",
                ),
            )
        ]

        if user.groups:
            access_conditions.append(
                FieldCondition(
                    key="allowed_groups",
                    match=MatchAny(
                        any=user.groups,
                    ),
                )
            )

        security_filter = Filter(
            must=[
                FieldCondition(
                    key="tenant_id",
                    match=MatchValue(
                        value=user.tenant_id,
                    ),
                ),
                Filter(
                    should=access_conditions,
                ),
            ]
        )

        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=security_filter,
            limit=self.limit,
            with_payload=True,
        )

        documents = []

        for point in result.points:
            if point.payload is None:
                continue

            document = Document.model_validate(
                point.payload
            )

            if document.tenant_id != user.tenant_id:
                continue

            if (
                document.allowed_groups
                and not set(
                    document.allowed_groups
                ).intersection(
                    user.groups
                )
            ):
                continue

            documents.append(
                document
            )

        return documents
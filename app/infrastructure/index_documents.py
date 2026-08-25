import asyncio

from app.infrastructure.in_memory_retriever import (
    InMemoryDocumentRetriever,
)

from app.infrastructure.qdrant_retriever import (
    QdrantDocumentRetriever,
)


async def main() -> None:
    source = InMemoryDocumentRetriever()

    retriever = QdrantDocumentRetriever()

    indexed_count = await retriever.index_documents(
        source.documents
    )

    print(
        f"Indexed {indexed_count} documents "
        f"in collection "
        f"'{retriever.collection_name}'."
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
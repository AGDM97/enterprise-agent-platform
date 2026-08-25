from app.domain.models import (
    ChatRequest,
    ChatResponse,
    Document,
    SourceReference,
)
from app.domain.providers import LLMProvider


class MockLLMProvider(LLMProvider):
    async def generate(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        last_message = request.messages[-1]

        return ChatResponse(
            content=(
                f"Resposta simulada para: "
                f"{last_message.content}"
            ),
            provider="mock",
            model="mock-model-v1",
            input_tokens=len(
                last_message.content.split()
            ),
            output_tokens=5,
        )

    async def generate_with_context(
        self,
        request: ChatRequest,
        documents: list[Document],
    ) -> ChatResponse:
        response = await self.generate(request)

        if not documents:
            return response.model_copy(
                update={
                    "content": (
                        "Não encontrei documentos autorizados "
                        "para responder à sua pergunta."
                    ),
                    "sources": [],
                }
            )

        context = "\n".join(
            f"{document.title}: {document.content}"
            for document in documents
        )

        sources = [
            SourceReference(
                document_id=document.document_id,
                title=document.title,
            )
            for document in documents
        ]

        return response.model_copy(
            update={
                "content": (
                    f"Resposta baseada nos documentos "
                    f"autorizados: {context}"
                ),
                "sources": sources,
            }
        )
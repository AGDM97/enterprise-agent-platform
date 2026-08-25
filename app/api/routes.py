import os

import httpx

from fastapi import (
    APIRouter,
    HTTPException,
)

from app.application.agent_harness import (
    AgentHarness,
)

from app.application.telemetry import (
    InMemoryTelemetry,
)

from app.domain.guardrails import (
    GuardrailViolationError,
    InputGuardrail,
)

from app.domain.models import (
    ChatRequest,
    ChatResponse,
)

from app.infrastructure.in_memory_retriever import (
    InMemoryDocumentRetriever,
)

from app.infrastructure.mock_provider import (
    MockLLMProvider,
)

from app.infrastructure.ollama_provider import (
    OllamaLLMProvider,
)

from app.infrastructure.qdrant_retriever import (
    QdrantDocumentRetriever,
)

from app.infrastructure.ticket_tool import (
    CreateTicketTool,
)


router = APIRouter()

telemetry = InMemoryTelemetry()

retriever_backend = os.getenv(
    "RETRIEVER_BACKEND",
    "memory",
)

if retriever_backend == "qdrant":
    retriever = QdrantDocumentRetriever()

elif retriever_backend == "memory":
    retriever = InMemoryDocumentRetriever()

else:
    raise ValueError(
        "Unsupported retriever backend: "
        f"{retriever_backend}"
    )

input_guardrail = InputGuardrail()

tools = [
    CreateTicketTool(),
]

harness = AgentHarness(
    provider=MockLLMProvider(),
    retriever=retriever,
    input_guardrail=input_guardrail,
    telemetry=telemetry,
    tools=tools,
)

ollama_harness = AgentHarness(
    provider=OllamaLLMProvider(),
    retriever=retriever,
    input_guardrail=input_guardrail,
    telemetry=telemetry,
    tools=tools,
)

harnesses = {
    "mock": harness,
    "ollama": ollama_harness,
}


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }


@router.post(
    "/v1/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
) -> ChatResponse:
    selected_harness = harnesses.get(
        request.provider
    )

    if selected_harness is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported provider: "
                f"{request.provider}"
            ),
        )

    try:
        return await selected_harness.execute(
            request
        )

    except GuardrailViolationError as error:
        raise HTTPException(
            status_code=403,
            detail=(
                "Request blocked by security policy."
            ),
        ) from error

    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "The requested LLM provider "
                "is unavailable."
            ),
        ) from error
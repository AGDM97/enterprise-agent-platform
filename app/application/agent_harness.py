from uuid import uuid4

from app.application.telemetry import InMemoryTelemetry
from app.domain.guardrails import InputGuardrail
from app.domain.models import (
    ChatRequest,
    ChatResponse,
    ToolExecutionRequest,
    ToolExecutionResult,
)
from app.domain.providers import LLMProvider
from app.domain.retrieval import DocumentRetriever
from app.domain.tools import Tool


class AgentHarness:
    def __init__(
        self,
        provider: LLMProvider,
        retriever: DocumentRetriever,
        input_guardrail: InputGuardrail,
        telemetry: InMemoryTelemetry,
        tools: list[Tool] | None = None,
    ) -> None:
        self.provider = provider
        self.retriever = retriever
        self.input_guardrail = input_guardrail
        self.telemetry = telemetry

        self.tools = {
            tool.name: tool
            for tool in (tools or [])
        }

    async def execute(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        trace_id = str(uuid4())

        with self.telemetry.span(
            name="agent_execution",
            trace_id=trace_id,
            attributes={
                "tenant_id": request.user.tenant_id,
                "groups_count": len(
                    request.user.groups
                ),
            },
        ):
            with self.telemetry.span(
                name="guardrail",
                trace_id=trace_id,
            ):
                self.input_guardrail.validate(
                    request
                )

            last_message = request.messages[-1]

            selected_tool = self._select_tool(
                last_message.content
            )

            if selected_tool is not None:
                if not request.approval_granted:
                    pending_result = ToolExecutionResult(
                        tool_name=selected_tool.name,
                        success=False,
                        message=(
                            "Human approval is required "
                            "before executing this tool."
                        ),
                        approval_required=True,
                    )

                    return ChatResponse(
                        content=pending_result.message,
                        provider="mock",
                        model="mock-model-v1",
                        input_tokens=len(
                            last_message.content.split()
                        ),
                        output_tokens=0,
                        trace_id=trace_id,
                        tool_execution=pending_result,
                    )

                with self.telemetry.span(
                    name="tool_execution",
                    trace_id=trace_id,
                    attributes={
                        "tool_name": selected_tool.name,
                    },
                ):
                    tool_request = ToolExecutionRequest(
                        tool_name=selected_tool.name,
                        user=request.user,
                        arguments={
                            "description": (
                                last_message.content
                            )
                        },
                    )

                    tool_result = (
                        await selected_tool.execute(
                            tool_request
                        )
                    )

                return ChatResponse(
                    content=tool_result.message,
                    provider="mock",
                    model="mock-model-v1",
                    input_tokens=len(
                        last_message.content.split()
                    ),
                    output_tokens=0,
                    trace_id=trace_id,
                    tool_execution=tool_result,
                )

            with self.telemetry.span(
                name="retrieval",
                trace_id=trace_id,
            ):
                documents = await self.retriever.search(
                    query=last_message.content,
                    user=request.user,
                )

            with self.telemetry.span(
                name="llm_generation",
                trace_id=trace_id,
                attributes={
                    "documents_count": len(
                        documents
                    ),
                },
            ):
                response = (
                    await self.provider.generate_with_context(
                        request=request,
                        documents=documents,
                    )
                )

            return response.model_copy(
                update={
                    "trace_id": trace_id,
                }
            )

    def _select_tool(
        self,
        message: str,
    ) -> Tool | None:
        normalized_message = message.casefold()

        ticket_patterns = (
            "abrir chamado",
            "criar chamado",
            "abrir ticket",
            "criar ticket",
        )

        if any(
            pattern in normalized_message
            for pattern in ticket_patterns
        ):
            return self.tools.get(
                "create_ticket"
            )

        return None
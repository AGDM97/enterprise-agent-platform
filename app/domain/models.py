from typing import Literal

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    groups: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]

    content: str = Field(
        min_length=1,
        max_length=4000,
    )


class ChatRequest(BaseModel):
    
    user: UserContext

    messages: list[ChatMessage] = Field(
        min_length=1,
        max_length=20,
    )

    provider: str = Field(
        default="mock",
        min_length=1,
    )

    temperature: float = Field(
        default=0.2,
        ge=0,
        le=2,
    )
    approval_granted: bool = False


class Document(BaseModel):
    document_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)

    title: str = Field(min_length=1)
    content: str = Field(min_length=1)

    allowed_groups: list[str] = Field(
        default_factory=list
    )


class SourceReference(BaseModel):
    document_id: str
    title: str


class ToolExecutionRequest(BaseModel):
    tool_name: str = Field(min_length=1)
    user: UserContext

    arguments: dict[str, str] = Field(
        default_factory=dict
    )


class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    message: str

    resource_id: str | None = None

    approval_required: bool = False


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)

    trace_id: str | None = None

    sources: list[SourceReference] = Field(
        default_factory=list
    )

    tool_execution: ToolExecutionResult | None = None
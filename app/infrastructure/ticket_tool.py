from uuid import uuid4

from app.domain.models import (
    ToolExecutionRequest,
    ToolExecutionResult,
)
from app.domain.tools import Tool


class CreateTicketTool(Tool):
    allowed_groups = {
        "engineering",
        "architecture",
    }

    @property
    def name(self) -> str:
        return "create_ticket"

    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        user_groups = set(request.user.groups)

        if not user_groups.intersection(
            self.allowed_groups
        ):
            return ToolExecutionResult(
                tool_name=self.name,
                success=False,
                message=(
                    "User is not authorized "
                    "to create tickets."
                ),
            )

        description = request.arguments.get(
            "description",
            ""
        ).strip()

        if not description:
            return ToolExecutionResult(
                tool_name=self.name,
                success=False,
                message=(
                    "Ticket description is required."
                ),
            )

        ticket_id = (
            f"TICKET-{uuid4().hex[:8].upper()}"
        )

        return ToolExecutionResult(
            tool_name=self.name,
            success=True,
            message=(
                "Ticket created successfully."
            ),
            resource_id=ticket_id,
        )
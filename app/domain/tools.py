from abc import ABC, abstractmethod

from app.domain.models import (
    ToolExecutionRequest,
    ToolExecutionResult,
)


class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        raise NotImplementedError
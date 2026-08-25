import json
import logging

from contextlib import contextmanager
from time import perf_counter
from typing import Any, Iterator


logger = logging.getLogger("enterprise_agent")


class InMemoryTelemetry:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    @contextmanager
    def span(
        self,
        name: str,
        trace_id: str,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[None]:
        started_at = perf_counter()

        try:
            yield

        except Exception as error:
            self._record(
                name=name,
                trace_id=trace_id,
                status="error",
                duration_ms=(
                    (perf_counter() - started_at) * 1000
                ),
                attributes={
                    **(attributes or {}),
                    "error_type": type(error).__name__,
                },
            )

            raise

        else:
            self._record(
                name=name,
                trace_id=trace_id,
                status="ok",
                duration_ms=(
                    (perf_counter() - started_at) * 1000
                ),
                attributes=attributes or {},
            )

    def _record(
        self,
        name: str,
        trace_id: str,
        status: str,
        duration_ms: float,
        attributes: dict[str, Any],
    ) -> None:
        event = {
            "span": name,
            "trace_id": trace_id,
            "status": status,
            "duration_ms": round(duration_ms, 3),
            "attributes": attributes,
        }

        self.events.append(event)

        logger.info(
            json.dumps(
                event,
                ensure_ascii=False,
            )
        )
import logging
import re

from app.domain.models import Document


logger = logging.getLogger(
    "enterprise_agent"
)


class OutputGuardrail:
    insufficient_evidence_message = (
        "Não encontrei evidências suficientes "
        "nos documentos autorizados."
    )

    citation_pattern = re.compile(
        r"\[([a-zA-Z0-9_-]+)\]"
    )

    def apply(
        self,
        content: str,
        documents: list[Document],
    ) -> str:
        normalized_content = content.strip()

        if not documents:
            return self.insufficient_evidence_message

        if (
            normalized_content
            == self.insufficient_evidence_message
        ):
            return normalized_content

        authorized_document_ids = {
            document.document_id
            for document in documents
        }

        cited_document_ids = set(
            self.citation_pattern.findall(
                normalized_content
            )
        )

        if not cited_document_ids:
            logger.warning(
                "Output guardrail triggered: "
                "response contains no document citations."
            )

            return self._build_extractive_response(
                documents
            )

        unauthorized_citations = (
            cited_document_ids
            - authorized_document_ids
        )

        if unauthorized_citations:
            logger.warning(
                "Output guardrail triggered: "
                "response contains unauthorized citations: %s",
                sorted(
                    unauthorized_citations
                ),
            )

            return self._build_extractive_response(
                documents
            )

        for line in normalized_content.splitlines():
            stripped_line = line.strip()

            if not stripped_line:
                continue

            if not self.citation_pattern.search(
                stripped_line
            ):
                logger.warning(
                    "Output guardrail triggered: "
                    "response contains an uncited line."
                )

                return self._build_extractive_response(
                    documents
                )

        return normalized_content

    def _build_extractive_response(
        self,
        documents: list[Document],
    ) -> str:
        excerpts = []

        for document in documents[:3]:
            first_sentence = re.split(
                r"(?<=[.!?])\s+",
                document.content.strip(),
                maxsplit=1,
            )[0]

            excerpts.append(
                (
                    f"- {first_sentence} "
                    f"[{document.document_id}]"
                )
            )

        return "\n".join(
            excerpts
        )
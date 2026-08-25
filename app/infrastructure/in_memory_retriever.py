import re
import unicodedata

from app.domain.models import Document, UserContext
from app.domain.retrieval import DocumentRetriever


class InMemoryDocumentRetriever(DocumentRetriever):
    def __init__(self) -> None:
        self.documents = [
            Document(
                document_id="doc-001",
                tenant_id="maitha",
                title="Arquitetura RAG corporativa",
                content=(
                    "RAG combina recuperação de documentos com "
                    "geração por modelos de linguagem. "
                    "A arquitetura deve aplicar filtros por tenant "
                    "e permissões de acesso."
                ),
                allowed_groups=[
                    "architecture",
                    "engineering",
                ],
            ),
            Document(
                document_id="doc-002",
                tenant_id="maitha",
                title="Política de segurança para agentes",
                content=(
                    "Agentes corporativos devem aplicar guardrails, "
                    "auditoria, aprovação humana e controle de acesso "
                    "às ferramentas."
                ),
                allowed_groups=[
                    "architecture",
                    "engineering",
                ],
            ),
            Document(
                document_id="doc-003",
                tenant_id="maitha",
                title="Informações financeiras confidenciais",
                content=(
                    "O orçamento financeiro do projeto é "
                    "confidencial e restrito ao departamento "
                    "financeiro."
                ),
                allowed_groups=[
                    "finance",
                ],
            ),
            Document(
                document_id="doc-004",
                tenant_id="outro-cliente",
                title="Arquitetura privada de outro cliente",
                content=(
                    "RAG e arquitetura confidencial de uma "
                    "organização diferente."
                ),
                allowed_groups=[
                    "architecture",
                ],
            ),
            Document(
                document_id="doc-005",
                tenant_id="maitha",
                title="Política geral da empresa",
                content=(
                    "Todos os colaboradores devem seguir as "
                    "políticas corporativas de segurança."
                ),
                allowed_groups=[],
            ),
        ]

    async def search(
        self,
        query: str,
        user: UserContext,
    ) -> list[Document]:
        query_terms = self._tokenize(query)

        results: list[Document] = []

        for document in self.documents:
            if document.tenant_id != user.tenant_id:
                continue

            if not self._user_can_access(
                document=document,
                user=user,
            ):
                continue

            document_terms = self._tokenize(
                f"{document.title} {document.content}"
            )

            if query_terms.intersection(document_terms):
                results.append(document)

        return results

    @staticmethod
    def _user_can_access(
        document: Document,
        user: UserContext,
    ) -> bool:
        if not document.allowed_groups:
            return True

        return bool(
            set(document.allowed_groups).intersection(
                user.groups
            )
        )

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        normalized = unicodedata.normalize(
            "NFKD",
            text.casefold(),
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        words = re.findall(
            r"\b\w+\b",
            normalized,
        )

        return {
            word
            for word in words
            if len(word) >= 3
        }
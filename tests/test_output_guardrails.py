from app.domain.models import Document

from app.domain.output_guardrails import (
    OutputGuardrail,
)


def build_documents() -> list[Document]:
    return [
        Document(
            document_id="doc-001",
            tenant_id="maitha",
            title="Arquitetura RAG",
            content=(
                "A arquitetura deve aplicar filtros "
                "por tenant e permissões de acesso."
            ),
            allowed_groups=[
                "architecture",
            ],
        ),
        Document(
            document_id="doc-002",
            tenant_id="maitha",
            title="Segurança de agentes",
            content=(
                "Agentes corporativos devem aplicar "
                "guardrails e aprovação humana."
            ),
            allowed_groups=[
                "architecture",
            ],
        ),
    ]


def test_output_guardrail_accepts_authorized_citations() -> None:
    guardrail = OutputGuardrail()

    content = (
        "- Aplique filtros por tenant. [doc-001]\n"
        "- Utilize aprovação humana. [doc-002]"
    )

    result = guardrail.apply(
        content=content,
        documents=build_documents(),
    )

    assert result == content


def test_output_guardrail_replaces_uncited_answer() -> None:
    guardrail = OutputGuardrail()

    content = (
        "Implemente criptografia militar, "
        "GDPR e autenticação multifator."
    )

    result = guardrail.apply(
        content=content,
        documents=build_documents(),
    )

    assert "[doc-001]" in result

    assert "[doc-002]" in result

    assert "GDPR" not in result

    assert "criptografia militar" not in result


def test_output_guardrail_rejects_unauthorized_citation() -> None:
    guardrail = OutputGuardrail()

    content = (
        "Informações confidenciais "
        "de outro cliente. [doc-999]"
    )

    result = guardrail.apply(
        content=content,
        documents=build_documents(),
    )

    assert "[doc-999]" not in result

    assert "[doc-001]" in result


def test_output_guardrail_rejects_uncited_extra_content() -> None:
    guardrail = OutputGuardrail()

    content = (
        "Aplique filtros por tenant. [doc-001]\n"
        "Também implemente GDPR e criptografia militar."
    )

    result = guardrail.apply(
        content=content,
        documents=build_documents(),
    )

    assert "GDPR" not in result

    assert "criptografia militar" not in result


def test_output_guardrail_accepts_exact_refusal() -> None:
    guardrail = OutputGuardrail()

    content = (
        "Não encontrei evidências suficientes "
        "nos documentos autorizados."
    )

    result = guardrail.apply(
        content=content,
        documents=build_documents(),
    )

    assert result == content


def test_output_guardrail_handles_missing_documents() -> None:
    guardrail = OutputGuardrail()

    result = guardrail.apply(
        content="Resposta inventada.",
        documents=[],
    )

    assert result == (
        "Não encontrei evidências suficientes "
        "nos documentos autorizados."
    )
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_chat_success() -> None:
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Explique o que é RAG.",
            }
        ],
        "provider": "mock",
        "temperature": 0.2,
    }

    response = client.post("/v1/chat", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert body["provider"] == "mock"
    assert body["model"] == "mock-model-v1"
    assert body["content"] == "Resposta simulada para: Explique o que é RAG."
    assert body["input_tokens"] == 5
    assert body["output_tokens"] == 5


def test_chat_rejects_empty_messages() -> None:
    payload = {
        "messages": [],
        "provider": "mock",
        "temperature": 0.2,
    }

    response = client.post("/v1/chat", json=payload)

    assert response.status_code == 422


def test_chat_rejects_invalid_role() -> None:
    payload = {
        "messages": [
            {
                "role": "cliente",
                "content": "Olá",
            }
        ],
        "provider": "mock",
        "temperature": 0.2,
    }

    response = client.post("/v1/chat", json=payload)

    assert response.status_code == 422
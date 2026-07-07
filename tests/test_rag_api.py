from __future__ import annotations

from fastapi.testclient import TestClient
from unittest.mock import patch

from medical_drug_agent.app.api.main import app


client = TestClient(app)


def test_rag_search_api_returns_evidences() -> None:
    fake_evidences = [
        {
            "content": "仅用于RAG功能测试：测试性交互风险片段。",
            "source": "本地RAG功能测试文档",
            "section": "测试性交互风险",
            "score": 0.91,
            "relative_path": "drug_instructions/test_drug_a.md",
            "chunk_id": "drug_instructions/test_drug_a.md::chunk-1",
        }
    ]

    with patch("medical_drug_agent.app.api.routes.rag_retriever.retrieve", return_value=fake_evidences):
        response = client.post("/api/rag/search", json={"query": "测试药A和测试药B能一起用吗", "top_k": 5})

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["data"]["rag_evidences"] == fake_evidences


def test_rag_search_api_rejects_empty_query() -> None:
    response = client.post("/api/rag/search", json={"query": " ", "top_k": 5})
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "error"
    assert payload["error_code"] == "INVALID_INPUT"

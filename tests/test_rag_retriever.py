from __future__ import annotations

import importlib.util
from unittest.mock import patch

from medical_drug_agent.app.constants import RAG_MODEL_PATH


def test_module_level_retrieve_import_and_delegates_to_retriever():
    from medical_drug_agent.app.rag.retriever import retrieve

    fake_evidences = [
        {
            "content": "仅用于RAG功能测试：测试性交互风险片段。",
            "source": "本地RAG功能测试文档",
            "section": "测试性交互风险",
            "score": 0.9,
            "relative_path": "drug_instructions/test_drug_a.md",
            "chunk_id": "drug_instructions/test_drug_a.md::chunk-1",
        }
    ]

    with patch("medical_drug_agent.app.rag.retriever.RAGRetriever.retrieve", return_value=fake_evidences):
        assert retrieve("测试药A和测试药B能一起用吗", top_k=3) == fake_evidences


def test_module_level_retrieve_returns_empty_list_for_empty_query():
    from medical_drug_agent.app.rag.retriever import retrieve

    assert retrieve("   ") == []


def test_rag_evidence_marks_placeholder_content():
    from medical_drug_agent.app.rag.retriever import RAGEvidence, is_placeholder_evidence

    evidence = RAGEvidence(
        content="待补充：请根据药品说明书或权威资料填写。",
        source="模板文档",
        section="禁忌",
        score=0.8,
        relative_path="drug_instructions/template.md",
        chunk_id="chunk-1",
        is_placeholder=is_placeholder_evidence("待补充：请根据药品说明书或权威资料填写。"),
    ).to_dict()

    assert evidence["is_placeholder"] is True


def test_drug_safety_rag_context_filters_placeholder_evidence():
    from medical_drug_agent.app.rag.context import retrieve_drug_safety_evidences

    fake_items = [
        {
            "content": "待补充：请根据药品说明书或权威资料填写。",
            "source": "模板文档",
            "section": "禁忌",
            "score": 0.8,
            "relative_path": "drug_instructions/template.md",
            "chunk_id": "chunk-1",
            "is_placeholder": True,
        },
        {
            "content": "仅用于RAG功能测试：测试性交互风险片段。",
            "source": "本地RAG功能测试文档",
            "section": "测试性交互风险",
            "score": 0.9,
            "relative_path": "drug_instructions/test_drug_a.md",
            "chunk_id": "chunk-2",
            "is_placeholder": False,
        },
    ]

    with patch("medical_drug_agent.app.rag.context.retrieve", return_value=fake_items):
        evidences = retrieve_drug_safety_evidences({"current_drugs": ["测试药A"], "new_drug": "测试药B"})

    assert len(evidences) == 1
    assert evidences[0]["relative_path"] == "drug_instructions/test_drug_a.md"


def test_rag_retrieves_test_drug_interaction_chunk():
    if importlib.util.find_spec("chromadb") is None:
        return
    if importlib.util.find_spec("sentence_transformers") is None:
        return
    if not RAG_MODEL_PATH.exists():
        return

    from medical_drug_agent.app.rag.retriever import RAGRetriever
    from scripts.build_rag_index import build_index

    build_index()

    retriever = RAGRetriever()
    evidences = retriever.retrieve("测试药A和测试药B能一起用吗", top_k=5)

    assert evidences
    assert any(
        ("test_drug_a.md" in item.get("relative_path", "") or "test_drug_b.md" in item.get("relative_path", ""))
        and "测试性交互风险" in item.get("content", "")
        for item in evidences
    )

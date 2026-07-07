from __future__ import annotations

import logging
from typing import Any

from medical_drug_agent.app.rag.retriever import retrieve


logger = logging.getLogger(__name__)


def build_drug_safety_rag_query(payload: dict[str, Any], state: dict[str, Any] | None = None) -> str:
    """Build a concise RAG query from the user case.

    RAG evidence is only used as supplemental report context. It must not
    decide or change the rule-engine risk level.
    """
    state = state or {}
    normalized_current = state.get("normalized_current_drugs") or []
    normalized_new = state.get("normalized_new_drug")

    current_names = _drug_names_from_normalized(normalized_current) or list(payload.get("current_drugs", []) or [])
    new_name = _drug_name_from_normalized(normalized_new) or str(payload.get("new_drug", "") or "")
    diseases = list(payload.get("diseases", []) or [])
    patient_factors = list(payload.get("patient_factors", []) or [])
    age = payload.get("age")

    query_parts = [
        f"当前用药：{_join(current_names)}",
        f"拟新增药物：{new_name or '暂无'}",
        f"基础疾病：{_join(diseases)}",
        f"特殊人群：{_join(patient_factors)}",
    ]
    if age is not None:
        query_parts.append(f"年龄：{age}")
    query_parts.append("请检索药品说明书、用药安全指南、相互作用、禁忌、不良反应、特殊人群用药和用药提醒相关证据。")
    return "；".join(query_parts)


def retrieve_drug_safety_evidences(
    payload: dict[str, Any],
    state: dict[str, Any] | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    query = build_drug_safety_rag_query(payload, state)
    try:
        evidences = retrieve(query, top_k=top_k)
        return [item for item in evidences if not item.get("is_placeholder")]
    except Exception as exc:  # pragma: no cover - retrieve already guards; keep workflow resilient.
        logger.warning("RAG evidence retrieval failed: %s", exc)
        return []


def _drug_names_from_normalized(values: list[Any]) -> list[str]:
    names: list[str] = []
    for value in values:
        name = _drug_name_from_normalized(value)
        if name:
            names.append(name)
    return names


def _drug_name_from_normalized(value: Any) -> str:
    if value is None:
        return ""
    zh_name = str(getattr(value, "zh_name", "") or "").strip()
    en_name = str(getattr(value, "en_name", "") or "").strip()
    if zh_name and en_name:
        return f"{zh_name}（{en_name}）"
    return zh_name or en_name or str(value or "").strip()


def _join(values: list[Any]) -> str:
    cleaned = [str(item).strip() for item in values if str(item or "").strip()]
    return "、".join(cleaned) if cleaned else "暂无"

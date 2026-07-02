from __future__ import annotations

import json
import re


def parse_llm_report_json(text: str) -> dict:
    cleaned = str(text or "").strip()
    if not cleaned:
        raise ValueError("LLM 返回为空，无法解析报告 JSON")

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM 返回不是合法 JSON：{exc}") from exc

    pharmacist_report = payload.get("pharmacist_report")
    patient_report = payload.get("patient_report")
    if not isinstance(pharmacist_report, str) or not pharmacist_report.strip():
        raise ValueError("LLM 返回缺少 pharmacist_report")
    if not isinstance(patient_report, str) or not patient_report.strip():
        raise ValueError("LLM 返回缺少 patient_report")
    return {
        "pharmacist_report": pharmacist_report,
        "patient_report": patient_report,
    }

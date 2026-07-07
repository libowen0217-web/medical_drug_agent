from __future__ import annotations

import os

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.llm.client import LLMClient, resolve_provider
from medical_drug_agent.app.llm.parser import parse_llm_report_json
from medical_drug_agent.app.llm.prompts import SYSTEM_PROMPT, build_report_polish_prompt
from medical_drug_agent.app.serialization import to_dict


class LLMReportAgent(BaseAgent):
    agent_name = "llm-report-agent"

    def __init__(self, enable_llm: bool = False, client: LLMClient | None = None) -> None:
        self.enable_llm = enable_llm
        self.client = client

    def run(self, state: dict) -> AgentResult:
        if not self.enable_llm:
            return AgentResult(
                agent_name=self.agent_name,
                status="skipped",
                output={},
                metadata={"llm_enabled": False, "llm_used": False},
            )
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        pharmacist_report = str(state.get("pharmacist_report", "") or "")
        patient_report = str(state.get("patient_report", "") or "")
        if not pharmacist_report or not patient_report:
            raise ValueError("模板报告缺失，无法执行 LLM 润色")

        patient_info = state.get("patient_info")
        risk_summary = state.get("risk_summary")
        response_data = {
            "current_drugs": [to_dict(item) for item in list(state.get("normalized_current_drugs", []) or [])],
            "new_drug": to_dict(state.get("normalized_new_drug")),
            "age": getattr(patient_info, "age", None),
            "diseases": list(getattr(patient_info, "diseases", []) or []),
            "overall_risk_level": getattr(risk_summary, "overall_risk_level", None),
            "risk_findings": [to_dict(item) for item in list(getattr(risk_summary, "findings", []) or [])],
            "evidence_items": [
                to_dict(item)
                for finding in list(getattr(risk_summary, "findings", []) or [])
                for item in list(getattr(finding, "evidence_items", []) or [])
            ],
            "rag_evidences": list(state.get("rag_evidences", []) or []),
            "pharmacist_report": pharmacist_report,
            "patient_report": patient_report,
        }

        client = self.client
        fallback_provider = self._resolve_provider_fallback(client)
        fallback_model = getattr(client, "model", None) or os.getenv("LLM_MODEL")

        try:
            client = client or LLMClient()
            llm_output = client.generate_text(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=build_report_polish_prompt(response_data),
            )
            parsed = parse_llm_report_json(llm_output)
            return {
                "pharmacist_report": parsed["pharmacist_report"],
                "patient_report": parsed["patient_report"],
                "llm_metadata": {
                    "llm_enabled": True,
                    "llm_used": True,
                    "llm_provider": client.provider,
                    "llm_model": client.model,
                    "llm_error": None,
                },
            }
        except Exception as exc:
            return {
                "pharmacist_report": pharmacist_report,
                "patient_report": patient_report,
                "llm_metadata": {
                    "llm_enabled": True,
                    "llm_used": False,
                    "llm_provider": fallback_provider,
                    "llm_model": fallback_model,
                    "llm_error": str(exc),
                },
            }

    @staticmethod
    def _resolve_provider_fallback(client: LLMClient | None) -> str | None:
        if client is not None:
            return getattr(client, "provider", None)

        base_url = str(os.getenv("LLM_BASE_URL") or "")
        provider = os.getenv("LLM_PROVIDER")
        try:
            return resolve_provider(provider, base_url)
        except Exception:
            return provider or None

from __future__ import annotations

from typing import Any

from medical_drug_agent.app.agents.audit_agent import AuditAgent
from medical_drug_agent.app.agents.base import AgentResult
from medical_drug_agent.app.agents.dose_check_agent import DoseCheckAgent
from medical_drug_agent.app.agents.drug_normalization_agent import DrugNormalizationAgent
from medical_drug_agent.app.agents.kg_query_agent import KGQueryAgent
from medical_drug_agent.app.agents.llm_report_agent import LLMReportAgent
from medical_drug_agent.app.agents.report_agent import ReportAgent
from medical_drug_agent.app.agents.risk_aggregation_agent import RiskAggregationAgent
from medical_drug_agent.app.agents.rule_check_agent import RuleCheckAgent
from medical_drug_agent.app.agents.safety_guard_agent import SafetyGuardAgent
from medical_drug_agent.app.api_contract import build_error_response, build_success_response
from medical_drug_agent.app.audit.logger import AuditLogger
from medical_drug_agent.app.serialization import to_dict


class SupervisorAgent:
    ENGINE_VERSION = "local-csv-mvp-v1"

    def __init__(
        self,
        use_graph: bool = False,
        enable_audit: bool = False,
        enable_llm: bool = True,
        knowledge_backend: str | None = None,
        agent_name: str = "community-pharmacy-multi-agent",
        agent_version: str = "multi-agent-v1",
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.use_graph = use_graph
        self.enable_audit = enable_audit
        self.enable_llm = enable_llm
        self.knowledge_backend = knowledge_backend
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.audit_logger = audit_logger or AuditLogger()
        self._last_llm_metadata = {"llm_enabled": enable_llm, "llm_used": False}
        self.core_agents = [
            DrugNormalizationAgent(),
            KGQueryAgent(knowledge_backend=knowledge_backend),
            RuleCheckAgent(),
            DoseCheckAgent(),
            RiskAggregationAgent(),
            ReportAgent(),
        ]
        self.llm_report_agent = LLMReportAgent(enable_llm=enable_llm)
        self.safety_guard_agent = SafetyGuardAgent()
        self.audit_agent = AuditAgent(audit_logger=self.audit_logger, enable_audit=enable_audit)

    def run(self, payload: dict) -> dict:
        validation_error = self._validate_payload(payload)
        if validation_error is not None:
            return self._build_error(
                error_code="INVALID_INPUT",
                message=validation_error,
                executed=[],
                failed=[],
                payload=payload,
                warnings=[],
            )

        state: dict[str, Any] = {"input_payload": self._sanitize_payload(payload)}
        executed: list[str] = []
        failed: list[str] = []
        warnings: list[str] = []
        self._last_llm_metadata = {"llm_enabled": self.enable_llm, "llm_used": False}

        for agent in self.core_agents:
            result = self._run_agent(agent, state, executed, failed)
            if result.status == "error":
                return self._build_error(
                    error_code=self._error_code(result),
                    message=result.error or f"{agent.agent_name} 执行失败",
                    executed=executed,
                    failed=failed,
                    payload=payload,
                    warnings=warnings,
                )

        llm_result = self._run_agent(self.llm_report_agent, state, executed, failed, critical=False)
        self._last_llm_metadata = self._llm_metadata_from_result(llm_result)
        state["llm_metadata"] = self._last_llm_metadata
        if llm_result.status == "error":
            warnings.append(f"{self.llm_report_agent.agent_name}: {llm_result.error}")

        safety_result = self._run_agent(self.safety_guard_agent, state, executed, failed)
        if safety_result.status == "error":
            return self._build_error(
                error_code=self._error_code(safety_result),
                message=safety_result.error or f"{self.safety_guard_agent.agent_name} 执行失败",
                executed=executed,
                failed=failed,
                payload=payload,
                warnings=warnings,
            )

        response = self._build_success(state, executed, failed, warnings)
        state["response_payload"] = response

        audit_result = self._run_agent(self.audit_agent, state, executed, failed, critical=False)
        if audit_result.status == "success":
            response["metadata"]["audit"] = (audit_result.output or {}).get("audit")
        elif audit_result.status == "error":
            warnings.append(f"{self.audit_agent.agent_name}: {audit_result.error}")
            response["metadata"]["multi_agent"]["agents_failed"] = failed
        if warnings:
            response["metadata"]["multi_agent"]["warnings"] = warnings
        return response

    def _run_agent(
        self,
        agent,
        state: dict[str, Any],
        executed: list[str],
        failed: list[str],
        critical: bool = True,
    ) -> AgentResult:
        result = agent.run(state)
        if result.status != "skipped":
            executed.append(result.agent_name)
        if result.status == "success":
            state.update(result.output or {})
        elif result.status == "error":
            failed.append(result.agent_name)
            if critical:
                return result
        return result

    def _build_success(
        self,
        state: dict[str, Any],
        executed: list[str],
        failed: list[str],
        warnings: list[str],
    ) -> dict:
        risk_summary = state["risk_summary"]
        risk_findings = [to_dict(item) for item in risk_summary.findings]
        dose_results = [to_dict(item) for item in list(state.get("dose_results", []) or [])]
        payload = state["input_payload"]
        kg_backend_metadata = dict(state.get("kg_backend_metadata", {}) or {})
        return build_success_response(
            data={
                "overall_risk_level": risk_summary.overall_risk_level,
                "normalized_current_drugs": [to_dict(item) for item in state["normalized_current_drugs"]],
                "normalized_new_drug": to_dict(state["normalized_new_drug"]),
                "risk_findings": risk_findings,
                "dose_results": dose_results,
                "pharmacist_report": str(state.get("pharmacist_report", "") or ""),
                "patient_report": str(state.get("patient_report", "") or ""),
                "safety_warnings": list(state.get("safety_warnings", []) or []),
            },
            metadata={
                "engine_version": self.ENGINE_VERSION,
                "current_drug_count": len(payload.get("current_drugs", []) or []),
                "disease_count": len(payload.get("diseases", []) or []),
                "risk_finding_count": len(risk_findings),
                "safety_warning_count": len(state.get("safety_warnings", []) or []),
                "has_dose_input": payload.get("dose") is not None,
                "kg_query_summary": to_dict(state.get("kg_query_summary", {})),
                "configured_knowledge_backend": kg_backend_metadata.get(
                    "configured_knowledge_backend",
                    self.knowledge_backend or "auto",
                ),
                "active_knowledge_backend": kg_backend_metadata.get("active_knowledge_backend", "csv"),
                "knowledge_backend": kg_backend_metadata.get("knowledge_backend", "csv"),
                "fallback_used": bool(kg_backend_metadata.get("fallback_used", False)),
                "fallback_reason": kg_backend_metadata.get("fallback_reason"),
                "execution_mode": "multi-agent",
                "multi_agent": self._build_multi_agent_metadata(executed, failed, warnings),
            },
            message="检查完成",
        )

    def _build_error(
        self,
        error_code: str,
        message: str,
        executed: list[str],
        failed: list[str],
        payload: dict[str, Any],
        warnings: list[str],
    ) -> dict:
        return build_error_response(
            error_code=error_code,
            message=message,
            metadata={
                "engine_version": self.ENGINE_VERSION,
                "current_drug_count": len(payload.get("current_drugs", []) or []),
                "disease_count": len(payload.get("diseases", []) or []),
                "risk_finding_count": 0,
                "safety_warning_count": 0,
                "has_dose_input": payload.get("dose") is not None,
                "configured_knowledge_backend": self.knowledge_backend or "auto",
                "active_knowledge_backend": "csv",
                "knowledge_backend": "csv",
                "fallback_used": False,
                "fallback_reason": None,
                "execution_mode": "multi-agent",
                "multi_agent": self._build_multi_agent_metadata(executed, failed, warnings),
            },
        )

    def _build_multi_agent_metadata(
        self,
        executed: list[str],
        failed: list[str],
        warnings: list[str],
    ) -> dict:
        metadata = {
            "enabled": True,
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "agents_executed": executed,
            "agents_failed": failed,
            "execution_mode": "multi-agent",
            "llm_enabled": bool(self._last_llm_metadata.get("llm_enabled", self.enable_llm)),
            "llm_used": bool(self._last_llm_metadata.get("llm_used", False)),
        }
        if self._last_llm_metadata.get("llm_error"):
            metadata["llm_error"] = self._last_llm_metadata["llm_error"]
        if self.use_graph:
            metadata["use_graph_requested"] = True
        if warnings:
            metadata["warnings"] = warnings
        return metadata

    def _llm_metadata_from_result(self, result: AgentResult) -> dict:
        if result.status == "skipped":
            return {"llm_enabled": False, "llm_used": False}
        output = result.output or {}
        metadata = dict(output.get("llm_metadata", {}) or {})
        metadata.setdefault("llm_enabled", self.enable_llm)
        metadata.setdefault("llm_used", False)
        return metadata

    @staticmethod
    def _sanitize_payload(payload: dict) -> dict:
        return {
            "current_drugs": list(payload.get("current_drugs", []) or []),
            "new_drug": str(payload.get("new_drug", "") or ""),
            "age": payload.get("age"),
            "diseases": list(payload.get("diseases", []) or []),
            "patient_factors": list(payload.get("patient_factors", []) or []),
            "dose": payload.get("dose"),
        }

    @staticmethod
    def _validate_payload(payload: dict) -> str | None:
        current_drugs = list(payload.get("current_drugs", []) or [])
        new_drug = str(payload.get("new_drug", "") or "")
        age = payload.get("age")
        dose = payload.get("dose")
        if not current_drugs:
            return "current_drugs 不能为空"
        if not new_drug.strip():
            return "new_drug 不能为空"
        if age is not None and age < 0:
            return "age 不能小于 0"
        if dose is not None and not isinstance(dose, dict):
            return "dose 必须为对象或 null"
        return None

    @staticmethod
    def _error_code(result: AgentResult) -> str:
        return str(result.metadata.get("error_code", "WORKFLOW_ERROR"))

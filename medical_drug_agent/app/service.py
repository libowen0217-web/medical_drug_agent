from __future__ import annotations

from medical_drug_agent.app.agents.supervisor_agent import SupervisorAgent
from medical_drug_agent.app.api_contract import build_error_response, build_success_response
from medical_drug_agent.app.audit.logger import AuditLogger
from medical_drug_agent.app.graph.graph import DrugSafetyLangGraph
from medical_drug_agent.app.schemas import DoseInput, DrugSafetyRequest, DrugSafetyResponse
from medical_drug_agent.app.serialization import to_dict
from medical_drug_agent.app.workflow import DrugSafetyWorkflow


class DrugSafetyService:
    """Stable local JSON-friendly service interface for the drug safety workflow."""

    ENGINE_VERSION = "local-csv-mvp-v1"

    def __init__(
        self,
        workflow: DrugSafetyWorkflow | None = None,
        audit_logger: AuditLogger | None = None,
        use_graph: bool = False,
    ) -> None:
        self.workflow = workflow or DrugSafetyWorkflow()
        self.audit_logger = audit_logger or AuditLogger()
        self.use_graph = use_graph
        self.graph = DrugSafetyLangGraph() if use_graph else None

    def check(self, request: DrugSafetyRequest) -> DrugSafetyResponse:
        validation_error = self._validate_request(request)
        if validation_error is not None:
            return self._response_from_dict(
                build_error_response(
                    error_code="INVALID_INPUT",
                    message=validation_error,
                    metadata={"engine_version": self.ENGINE_VERSION},
                )
            )

        try:
            normalized_current = self.workflow.mapper.normalize_many(request.current_drugs)
            normalized_new = self.workflow.mapper.normalize(request.new_drug)
            dose_inputs = self._build_dose_inputs(request)
            report_result = self.workflow.run(
                current_drugs=request.current_drugs,
                new_drug=request.new_drug,
                age=request.age,
                diseases=request.diseases,
                patient_factors=request.patient_factors,
                dose_inputs=dose_inputs,
            )
        except FileNotFoundError as exc:
            return self._response_from_dict(
                build_error_response(
                    error_code="DATA_FILE_MISSING",
                    message=str(exc),
                    metadata={"engine_version": self.ENGINE_VERSION},
                )
            )
        except ValueError as exc:
            return self._response_from_dict(
                build_error_response(
                    error_code="UNKNOWN_DRUG",
                    message=str(exc),
                    metadata={"engine_version": self.ENGINE_VERSION},
                )
            )
        except Exception as exc:
            return self._response_from_dict(
                build_error_response(
                    error_code="WORKFLOW_ERROR",
                    message=f"系统处理失败：{exc}",
                    metadata={"engine_version": self.ENGINE_VERSION},
                )
            )

        risk_findings = [to_dict(item) for item in report_result.risk_summary.findings]
        dose_results = [to_dict(item) for item in report_result.risk_summary.dose_results]
        safety_warnings = list(report_result.safety_warnings)
        has_dose_input = request.dose is not None

        response_dict = build_success_response(
            data={
                "overall_risk_level": report_result.risk_summary.overall_risk_level,
                "normalized_current_drugs": [to_dict(item) for item in normalized_current],
                "normalized_new_drug": to_dict(normalized_new),
                "risk_findings": risk_findings,
                "dose_results": dose_results,
                "pharmacist_report": report_result.pharmacist_report,
                "patient_report": report_result.patient_report,
                "safety_warnings": safety_warnings,
            },
            metadata={
                "engine_version": self.ENGINE_VERSION,
                "current_drug_count": len(request.current_drugs),
                "disease_count": len(request.diseases),
                "risk_finding_count": len(risk_findings),
                "safety_warning_count": len(safety_warnings),
                "has_dose_input": has_dose_input,
            },
            message="检查完成",
        )
        return self._response_from_dict(response_dict)

    def check_from_dict(self, payload: dict, enable_audit: bool = False) -> dict:
        if self.use_graph:
            try:
                response = self.graph.run(payload)
            except FileNotFoundError as exc:
                response = build_error_response(
                    error_code="DATA_FILE_MISSING",
                    message=str(exc),
                    metadata={"engine_version": self.ENGINE_VERSION},
                )
            except ValueError as exc:
                response = build_error_response(
                    error_code="UNKNOWN_DRUG",
                    message=str(exc),
                    metadata={"engine_version": self.ENGINE_VERSION},
                )
            except Exception as exc:
                response = build_error_response(
                    error_code="WORKFLOW_ERROR",
                    message=f"图工作流处理失败：{exc}",
                    metadata={"engine_version": self.ENGINE_VERSION},
                )
            return self._attach_audit(payload, response, enable_audit)

        try:
            request = DrugSafetyRequest(
                current_drugs=list(payload.get("current_drugs", []) or []),
                new_drug=str(payload.get("new_drug", "") or ""),
                age=payload.get("age"),
                diseases=list(payload.get("diseases", []) or []),
                patient_factors=list(payload.get("patient_factors", []) or []),
                dose=payload.get("dose"),
            )
        except Exception as exc:
            response = build_error_response(
                error_code="INVALID_INPUT",
                message=f"输入结构无效：{exc}",
                metadata={"engine_version": self.ENGINE_VERSION},
            )
            return self._attach_audit(payload, response, enable_audit)
        response = to_dict(self.check(request))
        return self._attach_audit(payload, response, enable_audit)

    def check_multi_agent_from_dict(
        self,
        payload: dict,
        enable_audit: bool = False,
        enable_llm: bool = True,
        knowledge_backend: str | None = None,
    ) -> dict:
        supervisor = SupervisorAgent(
            use_graph=self.use_graph,
            enable_audit=enable_audit,
            enable_llm=enable_llm,
            knowledge_backend=knowledge_backend,
            audit_logger=self.audit_logger,
        )
        return supervisor.run(payload)

    def _build_dose_inputs(self, request: DrugSafetyRequest) -> list[DoseInput] | None:
        if not request.dose:
            return None
        dose_mode = str(request.dose.get("dose_mode", "") or "").strip() or None
        return [
            DoseInput(
                drug_name=request.new_drug,
                single_dose_mg=request.dose.get("single_dose_mg"),
                times_per_day=request.dose.get("times_per_day"),
                duration_days=request.dose.get("duration_days"),
                dose_mode=dose_mode,
                allow_reference_dose=dose_mode == "label_reference",
                dose_context="drug_safety_otc" if dose_mode == "label_reference" else "drug_safety",
            )
        ]

    def _validate_request(self, request: DrugSafetyRequest) -> str | None:
        if not request.current_drugs:
            return "current_drugs 不能为空"
        if not request.new_drug or not request.new_drug.strip():
            return "new_drug 不能为空"
        if request.age is not None and request.age < 0:
            return "age 不能小于 0"
        if request.dose is not None and not isinstance(request.dose, dict):
            return "dose 必须为对象或 null"
        return None

    @staticmethod
    def _response_from_dict(payload: dict) -> DrugSafetyResponse:
        return DrugSafetyResponse(
            request_id=str(payload.get("request_id", "")),
            timestamp=str(payload.get("timestamp", "")),
            status=str(payload.get("status", "")),
            error_code=payload.get("error_code"),
            message=str(payload.get("message", "")),
            data=payload.get("data"),
            metadata=dict(payload.get("metadata", {}) or {}),
        )

    def _attach_audit(self, request_payload: dict, response_payload: dict, enable_audit: bool) -> dict:
        if not enable_audit:
            return response_payload
        audit_result = self.audit_logger.log_case(request_payload, response_payload)
        metadata = dict(response_payload.get("metadata", {}) or {})
        metadata["audit"] = audit_result
        response_payload["metadata"] = metadata
        return response_payload

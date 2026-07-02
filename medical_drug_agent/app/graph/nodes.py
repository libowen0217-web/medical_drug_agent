from __future__ import annotations

from typing import Any

from medical_drug_agent.app.api_contract import build_error_response, build_success_response
from medical_drug_agent.app.dose.checker import DoseChecker
from medical_drug_agent.app.knowledge.local_query_engine import LocalDrugQueryEngine
from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.reporting.aggregator import RiskAggregator
from medical_drug_agent.app.reporting.report_generator import TemplateReportGenerator
from medical_drug_agent.app.reporting.safety_filter import SafetyFilter
from medical_drug_agent.app.rules.engine import SafetyRuleEngine
from medical_drug_agent.app.schemas import DoseInput, PatientInfo
from medical_drug_agent.app.serialization import to_dict


ENGINE_VERSION = "local-csv-mvp-v1"

_MAPPER = DrugNameMapper()
_QUERY_ENGINE = LocalDrugQueryEngine(mapper=_MAPPER)
_RULE_ENGINE = SafetyRuleEngine()
_DOSE_CHECKER = DoseChecker(mapper=_MAPPER)
_AGGREGATOR = RiskAggregator()
_REPORT_GENERATOR = TemplateReportGenerator()
_SAFETY_FILTER = SafetyFilter()


def _has_error(state: dict[str, Any]) -> bool:
    return bool(state.get("error"))


def _set_error(state: dict[str, Any], error_code: str, message: str) -> dict[str, Any]:
    state["error"] = {"error_code": error_code, "message": message}
    return state


def validate_input_node(state: dict[str, Any]) -> dict[str, Any]:
    payload = dict(state.get("input_payload", {}) or {})
    current_drugs = list(payload.get("current_drugs", []) or [])
    new_drug = str(payload.get("new_drug", "") or "")
    age = payload.get("age")
    diseases = list(payload.get("diseases", []) or [])
    patient_factors = list(payload.get("patient_factors", []) or [])
    dose = payload.get("dose")

    state["current_drug_inputs"] = current_drugs
    state["new_drug_input"] = new_drug
    state["age"] = age
    state["diseases"] = diseases
    state["patient_factors"] = patient_factors
    state["dose"] = dose

    if not current_drugs:
        return _set_error(state, "INVALID_INPUT", "current_drugs 不能为空")
    if not new_drug.strip():
        return _set_error(state, "INVALID_INPUT", "new_drug 不能为空")
    if age is not None and age < 0:
        return _set_error(state, "INVALID_INPUT", "age 不能小于 0")
    if dose is not None and not isinstance(dose, dict):
        return _set_error(state, "INVALID_INPUT", "dose 必须为对象或 null")
    return state


def normalize_drugs_node(state: dict[str, Any]) -> dict[str, Any]:
    if _has_error(state):
        return state
    try:
        current_inputs = list(state.get("current_drug_inputs", []) or [])
        new_input = str(state.get("new_drug_input", "") or "")
        state["normalized_current_drugs"] = _MAPPER.normalize_many(current_inputs)
        state["normalized_new_drug"] = _MAPPER.normalize(new_input)
        state["patient_info"] = PatientInfo(
            age=state.get("age"),
            diseases=list(state.get("diseases", []) or []),
            patient_factors=list(state.get("patient_factors", []) or []),
        )
    except ValueError as exc:
        return _set_error(state, "UNKNOWN_DRUG", str(exc))
    except FileNotFoundError as exc:
        return _set_error(state, "DATA_FILE_MISSING", str(exc))
    except Exception as exc:
        return _set_error(state, "WORKFLOW_ERROR", f"图节点标准化失败：{exc}")
    return state


def query_kg_node(state: dict[str, Any]) -> dict[str, Any]:
    if _has_error(state):
        return state
    try:
        pair_relations = []
        current_inputs = list(state.get("current_drug_inputs", []) or [])
        new_input = str(state.get("new_drug_input", "") or "")
        for current_drug in current_inputs:
            pair_relations.extend(_QUERY_ENGINE.query_drug_pair(current_drug, new_input))
        state["kg_pair_relations"] = pair_relations
        state["kg_query_summary"] = {
            "relation_count": len(pair_relations),
            "current_drug_count": len(current_inputs),
        }
    except FileNotFoundError as exc:
        return _set_error(state, "DATA_FILE_MISSING", str(exc))
    except Exception as exc:
        return _set_error(state, "WORKFLOW_ERROR", f"图节点知识查询失败：{exc}")
    return state


def rule_check_node(state: dict[str, Any]) -> dict[str, Any]:
    if _has_error(state):
        return state
    try:
        state["rule_matches"] = _RULE_ENGINE.match_rules(
            current_drugs=list(state.get("normalized_current_drugs", []) or []),
            new_drug=state.get("normalized_new_drug"),
            patient=state.get("patient_info"),
        )
    except FileNotFoundError as exc:
        return _set_error(state, "DATA_FILE_MISSING", str(exc))
    except Exception as exc:
        return _set_error(state, "WORKFLOW_ERROR", f"图节点规则检查失败：{exc}")
    return state


def dose_check_node(state: dict[str, Any]) -> dict[str, Any]:
    if _has_error(state):
        return state
    try:
        new_drug_input = str(state.get("new_drug_input", "") or "")
        dose_payload = state.get("dose")
        dose_input = DoseInput(
            drug_name=new_drug_input,
            single_dose_mg=None if not dose_payload else dose_payload.get("single_dose_mg"),
            times_per_day=None if not dose_payload else dose_payload.get("times_per_day"),
            duration_days=None if not dose_payload else dose_payload.get("duration_days"),
        )
        state["dose_results"] = [_DOSE_CHECKER.check(dose_input)]
    except FileNotFoundError as exc:
        return _set_error(state, "DATA_FILE_MISSING", str(exc))
    except Exception as exc:
        return _set_error(state, "WORKFLOW_ERROR", f"图节点剂量检查失败：{exc}")
    return state


def aggregate_risk_node(state: dict[str, Any]) -> dict[str, Any]:
    if _has_error(state):
        return state
    try:
        state["risk_summary"] = _AGGREGATOR.aggregate(
            current_drugs=list(state.get("normalized_current_drugs", []) or []),
            new_drug=state.get("normalized_new_drug"),
            kg_pair_relations=list(state.get("kg_pair_relations", []) or []),
            rule_matches=list(state.get("rule_matches", []) or []),
            dose_results=list(state.get("dose_results", []) or []),
        )
    except Exception as exc:
        return _set_error(state, "WORKFLOW_ERROR", f"图节点风险汇总失败：{exc}")
    return state


def generate_report_node(state: dict[str, Any]) -> dict[str, Any]:
    if _has_error(state):
        return state
    try:
        pharmacist_report, patient_report = _REPORT_GENERATOR.generate(
            current_drugs=list(state.get("normalized_current_drugs", []) or []),
            new_drug=state.get("normalized_new_drug"),
            patient=state.get("patient_info"),
            risk_summary=state.get("risk_summary"),
        )
        state["pharmacist_report"] = pharmacist_report
        state["patient_report"] = patient_report
    except Exception as exc:
        return _set_error(state, "WORKFLOW_ERROR", f"图节点报告生成失败：{exc}")
    return state


def safety_filter_node(state: dict[str, Any]) -> dict[str, Any]:
    if _has_error(state):
        return state
    try:
        pharmacist_report, warnings_a = _SAFETY_FILTER.validate_and_fix(
            str(state.get("pharmacist_report", "") or "")
        )
        patient_report, warnings_b = _SAFETY_FILTER.validate_and_fix(
            str(state.get("patient_report", "") or "")
        )
        state["pharmacist_report"] = pharmacist_report
        state["patient_report"] = patient_report
        state["safety_warnings"] = list(warnings_a) + list(warnings_b)
    except Exception as exc:
        return _set_error(state, "WORKFLOW_ERROR", f"图节点安全过滤失败：{exc}")
    return state


def build_response_node(state: dict[str, Any]) -> dict[str, Any]:
    error = state.get("error")
    if error:
        state["response"] = build_error_response(
            error_code=str(error.get("error_code", "WORKFLOW_ERROR")),
            message=str(error.get("message", "图工作流处理失败")),
            metadata={"engine_version": ENGINE_VERSION},
        )
        return state

    risk_summary = state.get("risk_summary")
    normalized_current_drugs = list(state.get("normalized_current_drugs", []) or [])
    normalized_new_drug = state.get("normalized_new_drug")
    safety_warnings = list(state.get("safety_warnings", []) or [])
    diseases = list(state.get("diseases", []) or [])
    current_drug_inputs = list(state.get("current_drug_inputs", []) or [])
    dose = state.get("dose")

    risk_findings = [to_dict(item) for item in risk_summary.findings]
    response = build_success_response(
        data={
            "overall_risk_level": risk_summary.overall_risk_level,
            "normalized_current_drugs": [to_dict(item) for item in normalized_current_drugs],
            "normalized_new_drug": to_dict(normalized_new_drug),
            "risk_findings": risk_findings,
            "pharmacist_report": str(state.get("pharmacist_report", "") or ""),
            "patient_report": str(state.get("patient_report", "") or ""),
            "safety_warnings": safety_warnings,
        },
        metadata={
            "engine_version": ENGINE_VERSION,
            "current_drug_count": len(current_drug_inputs),
            "disease_count": len(diseases),
            "risk_finding_count": len(risk_findings),
            "safety_warning_count": len(safety_warnings),
            "has_dose_input": dose is not None,
            "execution_mode": "langgraph",
            "kg_query_summary": to_dict(state.get("kg_query_summary", {})),
        },
        message="检查完成",
    )
    state["response"] = response
    return state

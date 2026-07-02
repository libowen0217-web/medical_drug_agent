from __future__ import annotations

import traceback
from typing import Any

import streamlit as st

from medical_drug_agent.app.agents.supervisor_agent import SupervisorAgent
from medical_drug_agent.app.audit.logger import AuditLogger
from medical_drug_agent.app.symptom.symptom_workflow import SymptomConsultWorkflow
from medical_drug_agent.ui.ui_helpers import (
    DISEASE_OPTIONS,
    SPECIAL_FACTOR_OPTIONS,
    agent_name_to_label,
    build_drug_safety_payload,
    build_symptom_consult_payload,
    extract_api_ready_data,
    filter_drug_options_by_query,
    final_level_to_label,
    format_agent_list,
    format_drug_option,
    format_risk_findings,
    get_drug_value_from_option,
    get_nested,
    load_drug_options,
    normalize_special_factors,
    risk_level_to_color,
    risk_level_to_label,
    sex_to_label,
    status_to_label,
    validate_patient_context,
)


TITLE = "社区药店多智能体用药安全辅助系统"
SUBTITLE = "基于多智能体协作、药物安全规则、剂量检查、本地 RAG 证据和候选药协作评估的用药安全辅助系统"
DISCLAIMER = "本系统仅用于医生或药师的用药安全辅助参考，不构成诊断、处方或最终用药建议。"

DRUG_DEFAULTS = {
    "current_drugs": ["硝苯地平"],
    "new_drug": "布洛芬",
    "age": 68,
    "sex": "未知",
    "disease_options": ["高血压"],
    "disease_custom": "",
    "special_factors": [],
    "include_dose": False,
    "single_dose_mg": 400.0,
    "times_per_day": 3,
    "duration_days": 5,
}

DRUG_EXAMPLES = {
    "nifedipine_ibuprofen": {"current_drugs": ["硝苯地平"], "new_drug": "布洛芬"},
    "warfarin_ibuprofen": {"current_drugs": ["华法林"], "new_drug": "布洛芬"},
    "warfarin_aspirin": {"current_drugs": ["华法林"], "new_drug": "阿司匹林"},
}

SYMPTOM_DEFAULTS = {
    "symptom_text": "发热、头痛、嗓子疼，两天了",
    "age": 68,
    "sex": "未知",
    "temperature_c": 38.5,
    "duration_days": 2,
    "current_drugs": ["硝苯地平"],
    "disease_options": ["高血压"],
    "disease_custom": "",
    "special_factors": [],
    "allergies": "",
}

SYMPTOM_RED_FLAG_DEFAULTS = {
    "symptom_text": "发烧40度，胸痛，呼吸困难，意识有点模糊",
    "age": 70,
    "sex": "未知",
    "temperature_c": 40.0,
    "duration_days": 1,
    "current_drugs": ["硝苯地平"],
    "disease_options": ["高血压"],
    "disease_custom": "",
    "special_factors": ["老年人"],
    "allergies": "",
}


def _find_drug_label(display_name: str) -> str:
    for option in load_drug_options():
        if option["display_name"] == display_name:
            return option["label"]
    return display_name


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #F3F8FD 0%, #ECF5FE 100%);
        }
        .hero-card, .panel-card, .metric-card, .section-card {
            background: #FFFFFF;
            border: 1px solid #D9EAF7;
            border-radius: 18px;
            padding: 1rem 1.15rem;
            box-shadow: 0 8px 24px rgba(13, 71, 161, 0.08);
        }
        .hero-title {
            color: #0D47A1;
            font-size: 2rem;
            font-weight: 700;
        }
        .hero-subtitle {
            color: #1E88E5;
            font-size: 1rem;
            margin-top: 0.35rem;
        }
        .hero-note {
            color: #546E7A;
            font-size: 0.95rem;
            margin-top: 0.6rem;
        }
        .section-title {
            color: #0D47A1;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }
        .minor-title {
            color: #0D47A1;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }
        .metric-label {
            color: #607D8B;
            font-size: 0.9rem;
        }
        .metric-value {
            color: #0D47A1;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }
        .badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 999px;
            color: white;
            font-weight: 700;
            font-size: 0.88rem;
        }
        .risk-box-high {
            background: #FFF2F2;
            border-left: 4px solid #D32F2F;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            margin: 0.45rem 0;
        }
        .risk-box-medium {
            background: #FFF8ED;
            border-left: 4px solid #FB8C00;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            margin: 0.45rem 0;
        }
        .risk-box-low {
            background: #F2FBF5;
            border-left: 4px solid #2E7D32;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            margin: 0.45rem 0;
        }
        .risk-box-unknown {
            background: #F3F7FA;
            border-left: 4px solid #607D8B;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            margin: 0.45rem 0;
        }
        .info-box {
            background: #F5FAFF;
            border-left: 4px solid #1E88E5;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            margin: 0.45rem 0;
        }
        .blocked-box {
            background: #FFF1F1;
            border-left: 4px solid #D32F2F;
            border-radius: 10px;
            padding: 0.8rem 1rem;
            margin: 0.5rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state() -> None:
    drug_defaults_current = [_find_drug_label(name) for name in DRUG_DEFAULTS["current_drugs"]]
    drug_default_new = _find_drug_label(DRUG_DEFAULTS["new_drug"])
    symptom_defaults_current = [_find_drug_label(name) for name in SYMPTOM_DEFAULTS["current_drugs"]]
    symptom_red_flag_current = [_find_drug_label(name) for name in SYMPTOM_RED_FLAG_DEFAULTS["current_drugs"]]
    defaults = {
        "last_drug_safety_response": None,
        "last_symptom_consult_response": None,
        "last_debate_results": [],
        "last_medication_debate_summary": None,
        "settings_enable_llm": False,
        "settings_enable_audit": True,
        "settings_show_json": True,
        "settings_show_agent_chain": True,
        "settings_show_debug": False,
        "pending_drug_form": None,
        "pending_symptom_form": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    form_defaults = {
        "drug_current_drugs_multiselect": drug_defaults_current,
        "drug_new_drug_selectbox": drug_default_new,
        "drug_age_number_input": DRUG_DEFAULTS["age"],
        "drug_sex_selectbox": DRUG_DEFAULTS["sex"],
        "drug_disease_multiselect": DRUG_DEFAULTS["disease_options"],
        "drug_disease_custom_input": DRUG_DEFAULTS["disease_custom"],
        "drug_special_factors_multiselect": DRUG_DEFAULTS["special_factors"],
        "drug_include_dose_checkbox": DRUG_DEFAULTS["include_dose"],
        "drug_single_dose_input": DRUG_DEFAULTS["single_dose_mg"],
        "drug_times_per_day_input": DRUG_DEFAULTS["times_per_day"],
        "drug_duration_days_input": DRUG_DEFAULTS["duration_days"],
        "symptom_text_input": SYMPTOM_DEFAULTS["symptom_text"],
        "symptom_age_input": SYMPTOM_DEFAULTS["age"],
        "symptom_sex_selectbox": SYMPTOM_DEFAULTS["sex"],
        "symptom_temperature_input": SYMPTOM_DEFAULTS["temperature_c"],
        "symptom_duration_input": SYMPTOM_DEFAULTS["duration_days"],
        "symptom_current_drugs_multiselect": symptom_defaults_current,
        "symptom_disease_multiselect": SYMPTOM_DEFAULTS["disease_options"],
        "symptom_disease_custom_input": SYMPTOM_DEFAULTS["disease_custom"],
        "symptom_special_factors_multiselect": SYMPTOM_DEFAULTS["special_factors"],
        "symptom_allergies_input": SYMPTOM_DEFAULTS["allergies"],
    }
    for key, value in form_defaults.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("_symptom_red_flag_current_defaults", symptom_red_flag_current)


def _apply_pending_form_updates() -> None:
    pending_drug = st.session_state.get("pending_drug_form")
    if isinstance(pending_drug, dict):
        for key, value in pending_drug.items():
            st.session_state[key] = value
        st.session_state["pending_drug_form"] = None
    pending_symptom = st.session_state.get("pending_symptom_form")
    if isinstance(pending_symptom, dict):
        for key, value in pending_symptom.items():
            st.session_state[key] = value
        st.session_state["pending_symptom_form"] = None


def _queue_drug_form(values: dict[str, Any]) -> None:
    st.session_state["pending_drug_form"] = values


def _queue_symptom_form(values: dict[str, Any]) -> None:
    st.session_state["pending_symptom_form"] = values


def _make_drug_form_values(current_drugs: list[str], new_drug: str) -> dict[str, Any]:
    return {
        "drug_current_drugs_multiselect": [_find_drug_label(name) for name in current_drugs],
        "drug_new_drug_selectbox": _find_drug_label(new_drug),
    }


def _make_symptom_form_values(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "symptom_text_input": source["symptom_text"],
        "symptom_age_input": source["age"],
        "symptom_sex_selectbox": source["sex"],
        "symptom_temperature_input": source["temperature_c"],
        "symptom_duration_input": source["duration_days"],
        "symptom_current_drugs_multiselect": [_find_drug_label(name) for name in source["current_drugs"]],
        "symptom_disease_multiselect": source["disease_options"],
        "symptom_disease_custom_input": source["disease_custom"],
        "symptom_special_factors_multiselect": source["special_factors"],
        "symptom_allergies_input": source["allergies"],
    }


def _render_page_header() -> None:
    left, right = st.columns([5, 1.2])
    with left:
        st.markdown(
            f"""
            <div class="hero-card">
                <div class="hero-title">{TITLE}</div>
                <div class="hero-subtitle">{SUBTITLE}</div>
                <div class="hero-note">{DISCLAIMER}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("**当前模式**")
        st.caption("多智能体主路径")
        settings_container = st.popover("设置", use_container_width=True) if hasattr(st, "popover") else st.expander("设置", expanded=False)
        with settings_container:
            st.checkbox("启用 LLM 报告润色", key="settings_enable_llm")
            st.checkbox("启用审计日志", key="settings_enable_audit")
            st.checkbox("显示完整 JSON", key="settings_show_json")
            st.checkbox("显示 Agent 执行链路", key="settings_show_agent_chain")
            st.checkbox("显示调试信息", key="settings_show_debug")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_metric_overview(response: dict[str, Any]) -> None:
    parsed = extract_api_ready_data(response)
    data = parsed.get("data") or {}
    metadata = parsed.get("metadata") or {}
    multi_agent = get_nested(metadata, ["multi_agent"], default={}) or {}
    overall_risk = str(data.get("overall_risk_level", "unknown") or "unknown")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">运行状态</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{status_to_label(parsed.get("status", ""))}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">综合风险等级</div>', unsafe_allow_html=True)
        st.markdown(
            f'<span class="badge" style="background:{risk_level_to_color(overall_risk)};">{risk_level_to_label(overall_risk)}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">请求编号</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{parsed.get("request_id", "")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">时间戳</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{parsed.get("timestamp", "")}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">审计编号</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-value">{get_nested(metadata, ["audit", "audit_id"], default="-")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="metric-label">LLM 开关 / 实际使用</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-value">{multi_agent.get("llm_enabled", False)} / {multi_agent.get("llm_used", False)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


def _render_agent_chain(metadata: dict[str, Any]) -> None:
    multi_agent = get_nested(metadata, ["multi_agent"], default={}) or {}
    st.markdown("### 多智能体执行链路")
    st.write(f"执行模式：{multi_agent.get('execution_mode', metadata.get('execution_mode', '多智能体'))}")
    st.write(f"已执行智能体：{format_agent_list(multi_agent.get('agents_executed', []))}")
    st.write(f"失败智能体：{format_agent_list(multi_agent.get('agents_failed', []))}")


def _risk_box_class(risk_level: str) -> str:
    normalized = str(risk_level or "").strip().lower()
    if normalized == "high":
        return "risk-box-high"
    if normalized == "medium":
        return "risk-box-medium"
    if normalized == "low":
        return "risk-box-low"
    return "risk-box-unknown"


def _render_risk_findings(findings: list[dict[str, Any]]) -> None:
    st.markdown("### 风险发现")
    if not findings:
        st.info("当前没有可展示的风险发现。")
        return
    for index, finding in enumerate(findings, start=1):
        label = risk_level_to_label(str(finding.get("risk_level", "unknown")))
        with st.expander(f"{index}. {finding.get('title', '风险发现')} | {label}", expanded=index == 1):
            st.markdown(
                f"""
                <div class="{_risk_box_class(finding.get('risk_level', 'unknown'))}">
                <strong>{label}</strong><br/>
                描述：{finding.get("description", "")}<br/>
                机制：{finding.get("mechanism", "")}<br/>
                建议：{finding.get("recommendation", "")}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if finding.get("related_drugs"):
                st.write(f"相关药物：{', '.join(finding.get('related_drugs', []))}")
            if finding.get("related_diseases"):
                st.write(f"相关疾病：{', '.join(finding.get('related_diseases', []))}")


def _render_evidence_items(findings: list[dict[str, Any]]) -> None:
    st.markdown("### 证据引用")
    count = 0
    for finding in findings:
        for item in list(finding.get("evidence_items", []) or []):
            count += 1
            st.markdown(
                f"""
                <div class="info-box">
                <strong>{item.get("citation_label") or "[证据]"}</strong><br/>
                来源：{item.get("source_name", "")}<br/>
                证据内容：{item.get("evidence_text", "")}<br/>
                匹配分数：{item.get("score", "")} | 排名：{item.get("rank", "")}
                </div>
                """,
                unsafe_allow_html=True,
            )
    if count == 0:
        st.info("当前没有可展示的证据引用。")


def _render_reports(data: dict[str, Any]) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 药师版报告")
        st.text_area(
            "药师版报告内容",
            value=str(data.get("pharmacist_report", "") or ""),
            height=360,
            label_visibility="collapsed",
            key="drug_pharmacist_report_view",
        )
    with col2:
        st.markdown("### 患者版报告")
        st.text_area(
            "患者版报告内容",
            value=str(data.get("patient_report", "") or ""),
            height=360,
            label_visibility="collapsed",
            key="drug_patient_report_view",
        )


def _render_json_if_enabled(response: dict[str, Any], title: str, key: str) -> None:
    if bool(st.session_state.get("settings_show_json", True)):
        with st.expander(title, expanded=False):
            st.json(response)
    elif bool(st.session_state.get("settings_show_debug", False)):
        with st.expander(title, expanded=False):
            st.json(response)
    _ = key


def _show_error_response(response: dict[str, Any], json_key: str) -> None:
    parsed = extract_api_ready_data(response)
    st.error(f"{parsed.get('message', '请求失败')} (错误码：{parsed.get('error_code')})")
    _render_json_if_enabled(response, "查看完整 JSON", json_key)


def _collect_diseases(selected: list[str], custom_text: str) -> list[str]:
    values = list(selected or [])
    for item in [part.strip() for part in str(custom_text or "").replace("，", ",").split(",") if part.strip()]:
        if item not in values:
            values.append(item)
    return values


def _resolve_multiselect_drugs(selected_labels: list[str]) -> list[str]:
    return [get_drug_value_from_option(label) for label in list(selected_labels or [])]


def _call_drug_safety(payload: dict[str, Any]) -> dict[str, Any]:
    return SupervisorAgent(
        enable_audit=bool(st.session_state.get("settings_enable_audit", True)),
        enable_llm=bool(st.session_state.get("settings_enable_llm", False)),
    ).run(payload)


def _call_symptom_consult(payload: dict[str, Any]) -> dict[str, Any]:
    return SymptomConsultWorkflow(enable_audit=bool(st.session_state.get("settings_enable_audit", True))).run(payload)


def _render_drug_safety_tab() -> None:
    st.markdown("## 药物交互检查")
    options = load_drug_options()
    drug_query = st.text_input("搜索当前药库", key="drug_library_query_input", placeholder="输入中文药名、英文名、拼音或别名")
    filtered_options = filter_drug_options_by_query(drug_query, options)
    labels = [format_drug_option(option) for option in filtered_options]
    current_default = [label for label in st.session_state.get("drug_current_drugs_multiselect", []) if label in labels]
    new_default = st.session_state.get("drug_new_drug_selectbox", labels[0] if labels else "")

    left, right = st.columns([3, 7], gap="large")
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">药物信息</div>', unsafe_allow_html=True)
        st.caption("从当前药库中搜索并选择药物。")
        st.multiselect(
            "当前正在使用的药物",
            options=labels,
            default=[label for label in current_default if label in labels],
            key="drug_current_drugs_multiselect",
        )
        st.selectbox(
            "拟新增药物",
            options=labels,
            index=labels.index(new_default) if new_default in labels else 0,
            key="drug_new_drug_selectbox",
        )
        ex1, ex2, ex3 = st.columns(3)
        with ex1:
            if st.button("硝苯地平 + 布洛芬", key="drug_example_nifedipine_ibuprofen_btn", use_container_width=True):
                _queue_drug_form(_make_drug_form_values(["硝苯地平"], "布洛芬"))
                st.rerun()
        with ex2:
            if st.button("华法林 + 布洛芬", key="drug_example_warfarin_ibuprofen_btn", use_container_width=True):
                _queue_drug_form(_make_drug_form_values(["华法林"], "布洛芬"))
                st.rerun()
        with ex3:
            if st.button("华法林 + 阿司匹林", key="drug_example_warfarin_aspirin_btn", use_container_width=True):
                _queue_drug_form(_make_drug_form_values(["华法林"], "阿司匹林"))
                st.rerun()

        st.markdown('<div class="section-title" style="margin-top:1rem;">患者信息</div>', unsafe_allow_html=True)
        st.number_input("年龄", min_value=0, max_value=120, step=1, key="drug_age_number_input")
        st.selectbox("性别", options=["未知", "男", "女"], key="drug_sex_selectbox")
        st.multiselect("基础疾病", options=DISEASE_OPTIONS, key="drug_disease_multiselect")
        st.text_input("补充疾病", key="drug_disease_custom_input", placeholder="可选，逗号分隔")
        st.multiselect("特殊患者因素", options=SPECIAL_FACTOR_OPTIONS, key="drug_special_factors_multiselect")

        st.markdown('<div class="section-title" style="margin-top:1rem;">剂量信息</div>', unsafe_allow_html=True)
        st.checkbox("填写剂量信息", key="drug_include_dose_checkbox")
        if st.session_state.get("drug_include_dose_checkbox", False):
            st.number_input("单次剂量 mg", min_value=0.0, step=50.0, key="drug_single_dose_input")
            st.number_input("每日次数", min_value=1, step=1, key="drug_times_per_day_input")
            st.number_input("使用天数", min_value=1, step=1, key="drug_duration_days_input")

        if st.button("开始多智能体用药安全检查", key="drug_multi_agent_submit_btn", type="primary", use_container_width=True):
            st.session_state["drug_submit_requested"] = True
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        submit_requested = bool(st.session_state.pop("drug_submit_requested", False))
        selected_current = _resolve_multiselect_drugs(st.session_state.get("drug_current_drugs_multiselect", []))
        selected_new = get_drug_value_from_option(st.session_state.get("drug_new_drug_selectbox", ""))
        age = int(st.session_state.get("drug_age_number_input", 0))
        sex = str(st.session_state.get("drug_sex_selectbox", "未知"))
        diseases = _collect_diseases(
            list(st.session_state.get("drug_disease_multiselect", [])),
            str(st.session_state.get("drug_disease_custom_input", "")),
        )
        special_factors = list(st.session_state.get("drug_special_factors_multiselect", []))
        can_submit, warnings, errors = validate_patient_context(age, sex, special_factors)
        special_factors, auto_warnings = normalize_special_factors(age, sex, special_factors)
        warnings.extend(auto_warnings)
        for warning in warnings:
            st.warning(warning)
        for error in errors:
            st.error(error)

        if submit_requested and can_submit:
            payload = build_drug_safety_payload(
                current_drugs_text=selected_current,
                new_drug=selected_new,
                age=age,
                diseases_text=diseases,
                patient_factors_text=special_factors,
                include_dose=bool(st.session_state.get("drug_include_dose_checkbox", False)),
                single_dose_mg=st.session_state.get("drug_single_dose_input"),
                times_per_day=st.session_state.get("drug_times_per_day_input"),
                duration_days=st.session_state.get("drug_duration_days_input"),
            )
            try:
                st.session_state["last_drug_safety_response"] = _call_drug_safety(payload)
            except Exception as exc:
                st.error("页面调用失败")
                with st.expander("异常摘要", expanded=True):
                    st.code(f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")

        response = st.session_state.get("last_drug_safety_response")
        if not isinstance(response, dict):
            st.info("从左侧药库选择药物并提交后，这里会显示多智能体用药安全检查结果。")
            return

        parsed = extract_api_ready_data(response)
        if parsed.get("status") == "error":
            _show_error_response(response, "drug_error_json_expander")
            return

        data = parsed.get("data") or {}
        metadata = parsed.get("metadata") or {}
        findings = format_risk_findings(data.get("risk_findings", []))
        st.markdown("### 用药安全检查报告")
        _render_metric_overview(response)
        _render_risk_findings(findings)
        _render_evidence_items(findings)
        _render_reports(data)
        if bool(st.session_state.get("settings_show_agent_chain", True)):
            _render_agent_chain(metadata)
        _render_json_if_enabled(response, "查看完整 JSON", "drug_result_json_expander")


def _render_symptom_parsed(parsed_symptoms: list[dict[str, Any]]) -> None:
    st.markdown("### 症状解析结果")
    if not parsed_symptoms:
        st.info("当前没有识别到明确症状。")
        return
    for item in parsed_symptoms:
        st.markdown(
            f"""
            <div class="info-box">
            <strong>{item.get("symptom_name", "")}</strong><br/>
            命中关键词：{", ".join(item.get("matched_keywords", []) or [])}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_red_flags(response: dict[str, Any]) -> None:
    metadata = get_nested(response, ["metadata"], default={}) or {}
    data = get_nested(response, ["data"], default={}) or {}
    red_flag_triggered = bool(metadata.get("red_flag_triggered", False))
    red_flags = list(data.get("red_flags", []) or [])
    st.markdown("### 红旗症状筛查结果")
    if red_flag_triggered:
        st.markdown(
            '<div class="blocked-box"><strong>红旗症状已阻断 OTC 候选药展示和候选药协作评估</strong><br/>请优先由医生进一步评估。</div>',
            unsafe_allow_html=True,
        )
    else:
        st.success("当前未触发明确红旗症状阻断。")
    for item in red_flags:
        st.warning(f"[{item.get('urgency_level', '')}] {item.get('description', '')} | 处理提示：{item.get('action', '')}")


def _render_otc_candidates(otc_candidates: list[dict[str, Any]]) -> None:
    st.markdown("### OTC 候选药类别")
    if not otc_candidates:
        st.info("当前没有可展示的 OTC 候选药类别。")
        return
    for item in otc_candidates:
        st.markdown(
            f"""
            <div class="section-card">
            <div class="minor-title">{item.get("drug_class", "")}</div>
            <div>候选药物：{", ".join(item.get("candidate_drugs", []) or [])}</div>
            <div>注意事项：{item.get("caution", "")}</div>
            <div>说明：{item.get("reason", "")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_candidate_safety_results(candidate_safety_results: list[dict[str, Any]]) -> None:
    st.markdown("### 候选药安全检查结果")
    if not candidate_safety_results:
        st.info("当前没有可展示的候选药安全检查结果。")
        return
    for item in candidate_safety_results:
        safety_response = dict(item.get("safety_response", {}) or {})
        parsed = extract_api_ready_data(safety_response)
        data = parsed.get("data") or {}
        with st.expander(
            f"{item.get('candidate_drug', '')} | {risk_level_to_label(data.get('overall_risk_level', 'unknown'))}",
            expanded=False,
        ):
            st.write(f"综合风险等级：{risk_level_to_label(data.get('overall_risk_level', 'unknown'))}")
            for finding in format_risk_findings(data.get("risk_findings", []))[:3]:
                st.write(f"- {finding.get('title', '')}: {finding.get('description', '')}")


def _render_debate_summary_block(summary: dict[str, Any] | None) -> None:
    st.markdown("### 候选药协作评估摘要")
    if not isinstance(summary, dict):
        st.info("当前没有可展示的候选药协作评估摘要。")
        return
    if bool(summary.get("red_flag_blocked")):
        st.markdown(
            '<div class="blocked-box"><strong>红旗症状已阻断候选药协作评估</strong><br/>本轮不展示候选药排序。</div>',
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        f"""
        <div class="info-box">
        是否启用：{summary.get("debate_enabled", False)}<br/>
        结论：{summary.get("conclusion", "")}<br/>
        免责声明：{summary.get("disclaimer", "")}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_symptom_tab() -> None:
    st.markdown("## 症状问诊辅助")
    options = load_drug_options()
    symptom_query = st.text_input("搜索当前药库", key="symptom_library_query_input", placeholder="输入中文药名、英文名、拼音或别名")
    filtered_options = filter_drug_options_by_query(symptom_query, options)
    labels = [format_drug_option(option) for option in filtered_options]
    current_default = [
        label
        for label in st.session_state.get("symptom_current_drugs_multiselect", [])
        if label in labels
    ]

    left, right = st.columns([3, 7], gap="large")
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">输入信息</div>', unsafe_allow_html=True)
        st.text_area("症状描述", key="symptom_text_input", height=120)
        st.number_input("年龄", min_value=0, max_value=120, step=1, key="symptom_age_input")
        st.selectbox("性别", options=["未知", "男", "女"], key="symptom_sex_selectbox")
        st.number_input("体温", min_value=34.0, max_value=43.0, step=0.1, key="symptom_temperature_input")
        st.number_input("持续天数", min_value=0, max_value=60, step=1, key="symptom_duration_input")
        st.multiselect(
            "当前用药",
            options=labels,
            default=[label for label in current_default if label in labels],
            key="symptom_current_drugs_multiselect",
        )
        st.multiselect("基础疾病", options=DISEASE_OPTIONS, key="symptom_disease_multiselect")
        st.text_input("补充疾病", key="symptom_disease_custom_input")
        st.multiselect("特殊患者因素", options=SPECIAL_FACTOR_OPTIONS, key="symptom_special_factors_multiselect")
        st.text_input("过敏史", key="symptom_allergies_input")
        btn1, btn2, btn3 = st.columns(3)
        with btn1:
            if st.button("填入默认案例", key="symptom_default_case_btn", use_container_width=True):
                _queue_symptom_form(_make_symptom_form_values(SYMPTOM_DEFAULTS))
                st.rerun()
        with btn2:
            if st.button("填入红旗症状案例", key="symptom_red_flag_case_btn", use_container_width=True):
                _queue_symptom_form(_make_symptom_form_values(SYMPTOM_RED_FLAG_DEFAULTS))
                st.rerun()
        with btn3:
            if st.button("开始症状问诊辅助分析", key="symptom_submit_btn", type="primary", use_container_width=True):
                st.session_state["symptom_submit_requested"] = True
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        submit_requested = bool(st.session_state.pop("symptom_submit_requested", False))
        selected_current = _resolve_multiselect_drugs(st.session_state.get("symptom_current_drugs_multiselect", []))
        age = int(st.session_state.get("symptom_age_input", 0))
        sex = str(st.session_state.get("symptom_sex_selectbox", "未知"))
        special_factors = list(st.session_state.get("symptom_special_factors_multiselect", []))
        can_submit, warnings, errors = validate_patient_context(age, sex, special_factors)
        special_factors, auto_warnings = normalize_special_factors(age, sex, special_factors)
        warnings.extend(auto_warnings)
        for warning in warnings:
            st.warning(warning)
        for error in errors:
            st.error(error)

        if submit_requested and can_submit:
            payload = build_symptom_consult_payload(
                symptom_text=str(st.session_state.get("symptom_text_input", "")),
                age=age,
                sex={"未知": "unknown", "男": "male", "女": "female"}.get(sex, "unknown"),
                temperature_c=float(st.session_state.get("symptom_temperature_input", 0.0)),
                duration_days=int(st.session_state.get("symptom_duration_input", 0)),
                current_drugs_text=selected_current,
                diseases_text=_collect_diseases(
                    list(st.session_state.get("symptom_disease_multiselect", [])),
                    str(st.session_state.get("symptom_disease_custom_input", "")),
                ),
                patient_factors_text=special_factors,
                allergies_text=str(st.session_state.get("symptom_allergies_input", "")),
            )
            try:
                response = _call_symptom_consult(payload)
                st.session_state["last_symptom_consult_response"] = response
                parsed = extract_api_ready_data(response)
                data = parsed.get("data") or {}
                st.session_state["last_debate_results"] = list(data.get("debate_results", []) or [])
                st.session_state["last_medication_debate_summary"] = data.get("medication_debate_summary")
            except Exception as exc:
                st.error("页面调用失败")
                with st.expander("异常摘要", expanded=True):
                    st.code(f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")

        response = st.session_state.get("last_symptom_consult_response")
        if not isinstance(response, dict):
            st.info("完成一次症状问诊辅助分析后，这里会显示症状解析、红旗症状筛查和候选药协作评估结果。")
            return

        parsed = extract_api_ready_data(response)
        if parsed.get("status") == "error":
            _show_error_response(response, "symptom_error_json_expander")
            return

        data = parsed.get("data") or {}
        _render_symptom_parsed(list(data.get("parsed_symptoms", []) or []))
        _render_red_flags(response)
        _render_otc_candidates(list(data.get("otc_candidates", []) or []))
        _render_candidate_safety_results(list(data.get("candidate_safety_results", []) or []))
        _render_debate_summary_block(data.get("medication_debate_summary"))
        st.markdown("### 问诊辅助报告")
        st.text_area(
            "问诊辅助报告内容",
            value=str(data.get("consult_report", "") or ""),
            height=360,
            label_visibility="collapsed",
            key="symptom_consult_report_view",
        )
        _render_json_if_enabled(response, "查看完整 JSON", "symptom_result_json_expander")


def _render_debate_tab() -> None:
    st.markdown("## 候选药协作辩论")
    summary = st.session_state.get("last_medication_debate_summary")
    results = list(st.session_state.get("last_debate_results", []) or [])
    if not isinstance(summary, dict) and not results:
        st.info("请先在“症状问诊辅助”页面完成一次分析，然后查看候选药协作评估结果。")
        return

    _render_debate_summary_block(summary if isinstance(summary, dict) else None)
    if isinstance(summary, dict) and bool(summary.get("red_flag_blocked")):
        return
    st.markdown("### 候选药排序卡片")
    for index, item in enumerate(results, start=1):
        with st.expander(
            f"第 {item.get('rank', index)} 名 | {item.get('candidate_drug', '')}",
            expanded=index == 1,
        ):
            st.write(f"综合分数：{item.get('total_score', '')}")
            st.write(f"候选项等级：{final_level_to_label(item.get('final_level', ''))}")
            st.write(f"摘要：{item.get('summary', '')}")
            strengths = list(item.get("strengths", []) or [])
            cautions = list(item.get("cautions", []) or [])
            if strengths:
                st.markdown("**主要优势**")
                for value in strengths:
                    st.write(f"- {value}")
            if cautions:
                st.markdown("**主要注意事项**")
                for value in cautions:
                    st.write(f"- {value}")
            st.markdown("**各智能体观点**")
            for opinion in list(item.get("agent_opinions", []) or []):
                st.markdown(
                    f"""
                    <div class="info-box">
                    <strong>{agent_name_to_label(opinion.get("agent_name", ""))}</strong><br/>
                    分值变化：{opinion.get("score_delta", "")}<br/>
                    风险等级：{risk_level_to_label(opinion.get("risk_level", "unknown"))}<br/>
                    观点：{opinion.get("opinion", "")}<br/>
                    原因：{"；".join(opinion.get("reasons", []) or [])}<br/>
                    证据引用：{"；".join(opinion.get("evidence_refs", []) or [])}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _render_recent_response_debug(title: str, response: dict[str, Any] | None, json_key: str) -> None:
    st.markdown(f"### {title}")
    if not isinstance(response, dict):
        st.info("当前没有可展示的运行结果。")
        return
    parsed = extract_api_ready_data(response)
    metadata = parsed.get("metadata") or {}
    multi_agent = get_nested(metadata, ["multi_agent"], default={}) or {}
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"请求编号：{parsed.get('request_id', '')}")
        st.write(f"时间戳：{parsed.get('timestamp', '')}")
        st.write(f"运行状态：{status_to_label(parsed.get('status', ''))}")
        st.write(f"错误码：{parsed.get('error_code')}")
        st.write(f"审计编号：{get_nested(metadata, ['audit', 'audit_id'], default='-')}")
        st.write(f"工作流类型：{metadata.get('workflow_type', '-')}")
    with col2:
        st.write(f"红旗症状触发：{metadata.get('red_flag_triggered', False)}")
        st.write(f"候选药协作评估启用：{metadata.get('debate_enabled', False)}")
        st.write(f"LLM 开关：{multi_agent.get('llm_enabled', False)}")
        st.write(f"LLM 实际使用：{multi_agent.get('llm_used', False)}")
        st.write(f"已执行智能体：{format_agent_list(multi_agent.get('agents_executed', []))}")
        st.write(f"失败智能体：{format_agent_list(multi_agent.get('agents_failed', []))}")
        st.write(f"症状链路智能体：{format_agent_list(metadata.get('symptom_agents_executed', []))}")
        st.write(f"症状链路失败：{format_agent_list(metadata.get('symptom_agents_failed', []))}")
        st.write(f"辩论链路智能体：{format_agent_list(metadata.get('debate_agents_executed', []))}")
        st.write(f"辩论链路失败：{format_agent_list(metadata.get('debate_agents_failed', []))}")
    if bool(st.session_state.get("settings_show_json", True)) or bool(st.session_state.get("settings_show_debug", False)):
        with st.expander("查看 JSON", expanded=False):
            st.json(response)
    _ = json_key


def _render_debug_tab() -> None:
    st.markdown("## 系统调试与审计")
    latest_drug_response = st.session_state.get("last_drug_safety_response")
    audit_id = get_nested(latest_drug_response or {}, ["metadata", "audit", "audit_id"], default="")
    if audit_id:
        st.success("该请求已写入审计日志，可用于后续请求回放。")
    else:
        recent_logs = AuditLogger().load_all(limit=1)
        if recent_logs:
            st.caption(f"最近一条审计日志编号：{recent_logs[-1].get('audit_id', '')}")
    _render_recent_response_debug("最近一次药物交互检查", latest_drug_response, "debug_drug_json_expander")
    _render_recent_response_debug("最近一次症状问诊", st.session_state.get("last_symptom_consult_response"), "debug_symptom_json_expander")


def main() -> None:
    st.set_page_config(page_title=TITLE, page_icon="🩺", layout="wide")
    _init_session_state()
    _apply_pending_form_updates()
    _inject_styles()
    _render_page_header()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["药物交互检查", "症状问诊辅助", "候选药协作辩论", "系统调试与审计"]
    )
    with tab1:
        _render_drug_safety_tab()
    with tab2:
        _render_symptom_tab()
    with tab3:
        _render_debate_tab()
    with tab4:
        _render_debug_tab()


if __name__ == "__main__":
    main()

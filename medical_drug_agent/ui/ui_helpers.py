from __future__ import annotations

from functools import lru_cache
from typing import Any

from medical_drug_agent.app.normalization.mapper import DrugNameMapper

try:
    from pypinyin import Style, lazy_pinyin
except ImportError:  # pragma: no cover - optional dependency fallback
    Style = None
    lazy_pinyin = None


RISK_LEVEL_LABELS = {
    "high": "高风险",
    "medium": "中等风险",
    "low": "低风险",
    "unknown": "风险待确认",
}

RISK_LEVEL_COLORS = {
    "high": "#D32F2F",
    "medium": "#FB8C00",
    "low": "#2E7D32",
    "unknown": "#607D8B",
}

FINAL_LEVEL_LABELS = {
    "preferred_candidate": "当前规则下风险提示相对较少的候选项",
    "caution_candidate": "需要谨慎评估的候选项",
    "not_preferred_without_review": "未复核前不宜优先考虑的候选项",
}

STATUS_LABELS = {
    "success": "成功",
    "error": "错误",
}

SEX_LABELS = {
    "unknown": "未知",
    "male": "男",
    "female": "女",
}

AGENT_NAME_LABELS = {
    "symptom-fit-agent": "症状匹配智能体",
    "interaction-risk-agent": "交互风险智能体",
    "patient-factor-risk-agent": "患者因素智能体",
    "dose-reasoning-agent": "剂量推理智能体",
    "evidence-review-agent": "证据审查智能体",
    "medication-debate-manager-agent": "候选药协作管理智能体",
    "drug-normalization-agent": "药名标准化智能体",
    "kg-query-agent": "知识检索智能体",
    "rule-check-agent": "规则检查智能体",
    "dose-check-agent": "剂量检查智能体",
    "risk-aggregation-agent": "风险汇总智能体",
    "report-agent": "报告生成智能体",
    "llm-report-agent": "报告润色智能体",
    "safety-guard-agent": "安全过滤智能体",
    "symptom-intake-agent": "症状接收智能体",
    "red-flag-check-agent": "红旗症状筛查智能体",
    "otc-candidate-agent": "OTC 候选药智能体",
    "candidate-safety-agent": "候选药安全检查智能体",
    "symptom-consult-report-agent": "症状问诊报告智能体",
}

DISEASE_OPTIONS = [
    "高血压",
    "糖尿病",
    "胃溃疡",
    "肝功能异常",
    "肾功能不全",
    "哮喘",
    "冠心病",
]

SPECIAL_FACTOR_OPTIONS = ["儿童", "孕妇", "老年人"]

PINYIN_OVERRIDES = {
    "硝苯地平": "xiaobendiping",
    "氨氯地平": "anlvdiping",
    "缬沙坦": "xieshatan",
    "厄贝沙坦": "ebeishatan",
    "美托洛尔": "meituoluoer",
    "氢氯噻嗪": "qinglvsaiqin",
    "布洛芬": "buluofen",
    "阿司匹林": "asipilin",
    "双氯芬酸": "shuanglvfensuan",
    "塞来昔布": "sailaixibu",
    "对乙酰氨基酚": "duiyixiananjifen",
    "华法林": "huafalin",
    "二甲双胍": "erjiashuanggua",
    "阿托伐他汀": "atuofatating",
    "奥美拉唑": "aomeilazuo",
    "氯雷他定": "lvleitading",
    "西替利嗪": "xitiliqin",
    "氨溴索": "anxiusuo",
    "愈创甘油醚": "yuchuangganyoumi",
    "心痛定": "xintongding",
    "硝苯吡啶": "xiaobenbiding",
    "络活喜": "luohuoxi",
    "代文": "daiwen",
    "安博维": "anbowei",
    "倍他乐克": "beitaleke",
    "双氢克尿噻": "shuangqingkeniaosai",
    "芬必得": "fenbide",
    "美林": "meilin",
    "拜阿司匹灵": "baiasipiling",
    "扶他林": "futalin",
    "西乐葆": "xilebao",
    "扑热息痛": "purerexitong",
    "格华止": "gehuazhi",
    "立普妥": "liputuo",
    "洛赛克": "luosaike",
    "开瑞坦": "kairuitan",
}


def split_multivalue_text(text: str) -> list[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    normalized = raw
    for token in ["；", ";", "，", ",", "\n", "\r", "\t"]:
        normalized = normalized.replace(token, "|")
    values: list[str] = []
    seen: set[str] = set()
    for item in normalized.split("|"):
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            values.append(cleaned)
    return values


def risk_level_to_label(risk_level: str) -> str:
    return RISK_LEVEL_LABELS.get(str(risk_level or "").strip().lower(), RISK_LEVEL_LABELS["unknown"])


def risk_level_to_color(risk_level: str) -> str:
    return RISK_LEVEL_COLORS.get(str(risk_level or "").strip().lower(), RISK_LEVEL_COLORS["unknown"])


def final_level_to_label(final_level: str) -> str:
    return FINAL_LEVEL_LABELS.get(
        str(final_level or "").strip().lower(),
        "需要进一步复核的候选项",
    )


def status_to_label(status: str) -> str:
    return STATUS_LABELS.get(str(status or "").strip().lower(), str(status or "未知"))


def sex_to_label(sex: str) -> str:
    return SEX_LABELS.get(str(sex or "").strip().lower(), str(sex or "未知"))


def agent_name_to_label(agent_name: str) -> str:
    return AGENT_NAME_LABELS.get(str(agent_name or "").strip(), str(agent_name or "未知智能体"))


def _listify(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return split_multivalue_text(value)
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        cleaned = str(item).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            ordered.append(cleaned)
    return ordered


def _to_pinyin(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    if lazy_pinyin is not None and Style is not None:
        return "".join(lazy_pinyin(cleaned, style=Style.NORMAL))
    return PINYIN_OVERRIDES.get(cleaned, "")


@lru_cache(maxsize=1)
def load_drug_options() -> list[dict[str, Any]]:
    mapper = DrugNameMapper()
    options: list[dict[str, Any]] = []
    for item in mapper.list_supported_drugs():
        aliases = _dedupe([item.zh_name, item.en_name, *list(item.aliases or [])])
        pinyin = _to_pinyin(item.zh_name)
        option = {
            "display_name": item.zh_name,
            "standard_name": item.en_name,
            "aliases": aliases,
            "pinyin": pinyin,
        }
        option["label"] = format_drug_option(option)
        options.append(option)
    return options


def format_drug_option(option: dict[str, Any]) -> str:
    display_name = str(option.get("display_name", "") or "").strip()
    standard_name = str(option.get("standard_name", "") or "").strip()
    pinyin = str(option.get("pinyin", "") or "").strip()
    parts = [part for part in [display_name, standard_name, pinyin] if part]
    return " / ".join(parts)


def get_drug_value_from_option(label_or_option: str | dict[str, Any]) -> str:
    if isinstance(label_or_option, dict):
        return str(label_or_option.get("display_name", "") or label_or_option.get("standard_name", "") or "").strip()
    label = str(label_or_option or "").strip()
    for option in load_drug_options():
        if label == option["label"]:
            return str(option["display_name"])
    return label


def filter_drug_options_by_query(query: str, options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    q = str(query or "").strip().lower()
    if not q:
        return list(options)
    results: list[dict[str, Any]] = []
    for option in options:
        haystacks = [
            str(option.get("display_name", "")).lower(),
            str(option.get("standard_name", "")).lower(),
            str(option.get("pinyin", "")).lower(),
            " ".join(str(alias).lower() for alias in list(option.get("aliases", []) or [])),
            str(option.get("label", "")).lower(),
        ]
        if any(q in haystack for haystack in haystacks):
            results.append(option)
    return results


def validate_patient_context(age: int, sex: str, special_factors: list[str]) -> tuple[bool, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized_sex = str(sex or "").strip()
    factors = _dedupe(list(special_factors or []))

    if age < 14:
        warnings.append("当前年龄小于 14 岁，建议按儿童场景谨慎评估。")
    if age >= 65:
        warnings.append("当前年龄大于等于 65 岁，建议按老年人场景谨慎评估。")

    if age < 14 and "老年人" in factors:
        errors.append("年龄小于 14 岁时不能选择“老年人”。")
    if age >= 65 and "儿童" in factors:
        errors.append("年龄大于等于 65 岁时不能选择“儿童”。")
    if normalized_sex == "男" and "孕妇" in factors:
        errors.append("性别为“男”时不能选择“孕妇”。")
    if "孕妇" in factors and (age < 12 or age > 55):
        errors.append("当前年龄与“孕妇”场景明显不符，请先核实患者信息。")

    can_submit = not errors
    return can_submit, warnings, errors


def normalize_special_factors(age: int, sex: str, special_factors: list[str]) -> tuple[list[str], list[str]]:
    normalized = _dedupe(list(special_factors or []))
    warnings: list[str] = []
    if age < 14 and "儿童" not in normalized:
        normalized.append("儿童")
        warnings.append("已按儿童场景补充患者因素。")
    if age >= 65 and "老年人" not in normalized:
        normalized.append("老年人")
        warnings.append("已按老年人场景补充患者因素。")
    _ = sex
    return normalized, warnings


def build_drug_safety_payload(
    current_drugs_text: str | list[str],
    new_drug: str,
    age: int | None,
    diseases_text: str | list[str] = "",
    patient_factors_text: str | list[str] = "",
    include_dose: bool = False,
    single_dose_mg: float | None = None,
    times_per_day: int | None = None,
    duration_days: int | None = None,
) -> dict[str, Any]:
    dose = None
    if include_dose:
        dose = {
            "single_dose_mg": single_dose_mg,
            "times_per_day": times_per_day,
            "duration_days": duration_days,
        }
    return {
        "current_drugs": _listify(current_drugs_text),
        "new_drug": str(new_drug or "").strip(),
        "age": age,
        "diseases": _listify(diseases_text),
        "patient_factors": _listify(patient_factors_text),
        "dose": dose,
    }


def build_symptom_consult_payload(
    symptom_text: str,
    age: int | None,
    sex: str | None,
    temperature_c: float | None,
    duration_days: int | None,
    current_drugs_text: str | list[str] = "",
    diseases_text: str | list[str] = "",
    patient_factors_text: str | list[str] = "",
    allergies_text: str | list[str] = "",
) -> dict[str, Any]:
    return {
        "symptom_text": str(symptom_text or "").strip(),
        "age": age,
        "sex": str(sex or "").strip() or None,
        "temperature_c": temperature_c,
        "duration_days": duration_days,
        "current_drugs": _listify(current_drugs_text),
        "diseases": _listify(diseases_text),
        "patient_factors": _listify(patient_factors_text),
        "allergies": _listify(allergies_text),
    }


def extract_api_ready_data(response: dict[str, Any]) -> dict[str, Any]:
    payload = dict(response or {})
    return {
        "request_id": payload.get("request_id", ""),
        "timestamp": payload.get("timestamp", ""),
        "status": payload.get("status", ""),
        "error_code": payload.get("error_code"),
        "message": payload.get("message", ""),
        "data": payload.get("data") if isinstance(payload.get("data"), dict) else payload.get("data"),
        "metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
    }


def get_nested(data: dict[str, Any] | None, path: list[str], default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def format_agent_list(agents: list[str] | None) -> str:
    values = [agent_name_to_label(item) for item in list(agents or []) if str(item).strip()]
    return " -> ".join(values) if values else "无"


def format_risk_findings(findings: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    for finding in findings or []:
        item = dict(finding or {})
        formatted.append(
            {
                "title": item.get("title", ""),
                "risk_level": item.get("risk_level", "unknown"),
                "description": item.get("description", ""),
                "mechanism": item.get("mechanism", ""),
                "recommendation": item.get("recommendation", ""),
                "related_drugs": list(item.get("related_drugs", []) or []),
                "related_diseases": list(item.get("related_diseases", []) or []),
                "evidence_items": list(item.get("evidence_items", []) or []),
                "source": item.get("source", ""),
            }
        )
    return formatted


def build_demo_payload(
    current_drugs: list[str],
    new_drug: str,
    age: int | None,
    diseases: list[str],
    patient_factors: list[str],
    include_dose: bool = False,
    single_dose_mg: float | None = None,
    times_per_day: int | None = None,
    duration_days: int | None = None,
) -> dict[str, Any]:
    return build_drug_safety_payload(
        current_drugs_text=current_drugs,
        new_drug=new_drug,
        age=age,
        diseases_text=diseases,
        patient_factors_text=patient_factors,
        include_dose=include_dose,
        single_dose_mg=single_dose_mg,
        times_per_day=times_per_day,
        duration_days=duration_days,
    )


def extract_data(response: dict[str, Any]) -> dict[str, Any]:
    return extract_api_ready_data(response)

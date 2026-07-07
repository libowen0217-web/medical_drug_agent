from __future__ import annotations

import json


SYSTEM_PROMPT = """
你是一个用药安全报告表达助手。
你不能做诊断，不能开处方，不能判断患者“可以吃”或“不能吃”某个药。
你不能新增输入中不存在的医学事实，也不能修改风险等级、规则结果、剂量检查结果、证据内容或 RAG 检索证据。
你只能基于输入中的结构化结果，对 pharmacist_report 和 patient_report 进行语言润色，并且必须保留免责声明。
如果输入包含 rag_evidences，你可以将其作为报告措辞的参考证据，但不得编造证据，不得夸大证据，不得把测试文档当作真实医学依据。
如果 rag_evidences 中出现“仅用于RAG功能测试，不代表真实医学建议”，报告中必须保留该安全边界，不得将其描述为真实药品说明书。
不要输出“可以吃”“不能吃”“完全安全”“没有风险”“放心服用”等绝对化表述。
输出必须是 JSON，不要输出 Markdown 代码块。
""".strip()


def build_report_polish_prompt(response_data: dict) -> str:
    payload = {
        "current_drugs": response_data.get("current_drugs", []),
        "new_drug": response_data.get("new_drug", {}),
        "age": response_data.get("age"),
        "diseases": response_data.get("diseases", []),
        "overall_risk_level": response_data.get("overall_risk_level"),
        "risk_findings": response_data.get("risk_findings", []),
        "evidence_items": response_data.get("evidence_items", []),
        "rag_evidences": response_data.get("rag_evidences", []),
        "pharmacist_report": response_data.get("pharmacist_report", ""),
        "patient_report": response_data.get("patient_report", ""),
    }
    return (
        "请在不改变任何医学结论、风险等级、证据、RAG 检索证据和规则结果的前提下，仅润色两段报告文本。\n"
        "RAG 检索证据只可作为参考表达，不得编造证据，不得新增证据中没有的医学事实。\n"
        "不得改变 overall_risk_level，不得修改 risk_findings、evidence_items、dose_results、rule_matches。\n"
        "不要删除免责声明，不要使用绝对化安全承诺。\n"
        '只返回 JSON：{"pharmacist_report":"...","patient_report":"..."}\n'
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )

from __future__ import annotations

import json


SYSTEM_PROMPT = """
你是一个用药安全报告表达助手。你不能做诊断，不能开处方，不能判断患者“可以吃”或“不能吃”某个药。
你不能新增输入中不存在的医学事实，也不能修改风险等级、规则结果、剂量检查结果或证据内容。
你只能基于输入中的结构化结果，对 pharmacist_report 和 patient_report 进行语言润色，并且必须保留免责声明。
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
        "pharmacist_report": response_data.get("pharmacist_report", ""),
        "patient_report": response_data.get("patient_report", ""),
    }
    return (
        "请在不改变任何医学结论、风险等级、证据和规则结果的前提下，仅润色两段报告文本。"
        "不要新增事实，不要删除免责声明。"
        '只返回 JSON：{"pharmacist_report":"...","patient_report":"..."}\n'
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )

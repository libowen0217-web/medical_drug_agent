from __future__ import annotations


class SafetyFilter:
    """Replace risky absolute wording and append required disclaimers."""

    DISCLAIMER_1 = "本报告仅为用药安全辅助参考，不构成诊断或处方建议。"
    DISCLAIMER_2 = "以上分析基于本地知识图谱数据、规则匹配和证据摘要，可能不覆盖所有已知风险，请以医生、药师和药品说明书为准。"

    REPLACEMENTS = {
        "你可以吃": "是否适合使用需由医生或药师结合具体情况判断",
        "可以吃": "是否适合使用需由医生或药师结合具体情况判断",
        "你不能吃": "不建议自行使用，需咨询医生或药师",
        "不能吃": "不建议自行使用，需咨询医生或药师",
        "没有风险": "未在当前规则中发现明确信号，但仍需结合说明书和个体情况审慎评估",
        "没风险": "未在当前规则中发现明确信号，但仍需结合说明书和个体情况审慎评估",
        "完全安全": "仍需结合说明书、剂量和患者情况判断",
        "可以放心服用": "是否适合使用仍需结合说明书和个体情况确认",
        "放心服用": "是否适合使用仍需结合说明书和个体情况确认",
        "直接换成": "可咨询医生或药师是否考虑",
        "建议服用": "用药方案需由医生或药师确认",
        "推荐服用": "用药方案需由医生或药师确认",
        "建议按此剂量服用": "最终剂量需由医生或药师结合患者情况确认",
        "可以使用该剂量": "最终剂量需由医生或药师结合患者情况确认",
        "推荐剂量": "参考剂量",
        "最佳剂量": "参考剂量",
        "保证安全": "仍需结合说明书和个体情况进一步确认",
    }

    def validate_and_fix(self, text: str) -> tuple[str, list[str]]:
        warnings: list[str] = []
        fixed_text = text

        for bad, replacement in self.REPLACEMENTS.items():
            if bad in fixed_text:
                fixed_text = fixed_text.replace(bad, replacement)
                warnings.append(f"检测到并替换了禁止表述：{bad}")

        if self.DISCLAIMER_1 not in fixed_text:
            fixed_text = f"{fixed_text}\n\n{self.DISCLAIMER_1}"
            warnings.append("已补充免责声明 1")

        if self.DISCLAIMER_2 not in fixed_text:
            fixed_text = f"{fixed_text}\n{self.DISCLAIMER_2}"
            warnings.append("已补充免责声明 2")

        return fixed_text, warnings

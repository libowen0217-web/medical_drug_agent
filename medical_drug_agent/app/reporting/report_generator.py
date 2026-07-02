from __future__ import annotations

from medical_drug_agent.app.schemas import DrugInfo, PatientInfo, RiskSummary


class TemplateReportGenerator:
    """Generate pharmacist and patient reports using deterministic templates."""

    DISCLAIMER_1 = "本报告仅为用药安全辅助参考，不构成诊断或处方建议。"
    DISCLAIMER_2 = "以上分析基于本地知识图谱数据、规则匹配和证据摘要，可能不覆盖所有已知风险，请以医生、药师和药品说明书为准。"
    DOSE_REFERENCE_DISCLAIMER = (
        "本次未提供实际剂量，系统基于说明书参考剂量进行初步模拟评估。"
        "该剂量不代表患者实际用药剂量，最终剂量需由医生或药师结合患者情况确认。"
    )
    DOSE_MISSING_DISCLAIMER = "未提供实际剂量，且当前药物未找到可用参考剂量，因此剂量相关判断仅作缺失提示。"

    def generate(
        self,
        current_drugs: list[DrugInfo],
        new_drug: DrugInfo,
        patient: PatientInfo,
        risk_summary: RiskSummary,
    ) -> tuple[str, str]:
        pharmacist_report = self._build_pharmacist_report(current_drugs, new_drug, patient, risk_summary)
        patient_report = self._build_patient_report(current_drugs, new_drug, patient, risk_summary)
        return pharmacist_report, patient_report

    def _build_pharmacist_report(
        self,
        current_drugs: list[DrugInfo],
        new_drug: DrugInfo,
        patient: PatientInfo,
        risk_summary: RiskSummary,
    ) -> str:
        lines = [
            "社区药店用药安全检查报告（药师版）",
            "",
            (
                f"患者信息：年龄={patient.age if patient.age is not None else '未提供'}；"
                f"疾病={', '.join(patient.diseases) if patient.diseases else '未提供'}；"
                f"患者因素={', '.join(patient.patient_factors) if patient.patient_factors else '未提供'}"
            ),
            f"当前用药：{', '.join(drug.zh_name for drug in current_drugs)}",
            f"拟新增用药：{new_drug.zh_name}（{new_drug.en_name}）",
            f"综合风险等级：{risk_summary.overall_risk_level}",
            f"知识图谱关系提示：检索到直接关系 {risk_summary.kg_relation_count} 条",
            "",
            "规则命中结果：",
        ]

        if risk_summary.rule_matches:
            for match in risk_summary.rule_matches:
                lines.extend(
                    [
                        f"- [{match.risk_level}] {match.risk}",
                        f"  原因：{match.matched_reason}",
                        f"  机制：{match.mechanism}",
                        f"  处理提示：{match.recommendation}",
                    ]
                )
        else:
            lines.append("- 未命中本地规则。")

        evidence_findings = [finding for finding in risk_summary.findings if finding.evidence_items]
        if evidence_findings:
            lines.extend(["", "证据提示："])
            for finding in evidence_findings:
                lines.append(f"- {finding.title}")
                for item in finding.evidence_items:
                    label = item.citation_label or "[证据]"
                    lines.append(f"  - {label} 来源：{item.source_name}。{item.evidence_text}")

        lines.extend(["", "剂量检查结果："])
        if risk_summary.dose_results:
            for result in risk_summary.dose_results:
                lines.append(f"- [{result.risk_level}] {result.message}")
                lines.append(f"  剂量来源：{result.dose_source_label}")
                if result.reference_dose:
                    lines.append(
                        "  参考剂量："
                        f"单次 {result.reference_dose.get('single_dose_mg')} mg，"
                        f"每日 {result.reference_dose.get('times_per_day')} 次，"
                        f"使用 {result.reference_dose.get('duration_days')} 天"
                    )
        else:
            lines.append("- 未提供剂量检查结果。")

        dose_reference_used = any(result.dose_source == "label_reference" for result in risk_summary.dose_results)
        dose_missing_without_reference = any(
            result.dose_source == "missing" and result.status == "missing_dose" for result in risk_summary.dose_results
        )

        lines.extend(
            [
                "",
                "综合处理建议：",
                "- 请结合知识图谱关系、本地规则命中情况、剂量信息和药品说明书进一步确认。",
                "- 如涉及高风险或信息不足场景，建议咨询医生或由执业药师进一步评估。",
            ]
        )

        if dose_reference_used:
            lines.append(f"- {self.DOSE_REFERENCE_DISCLAIMER}")
        elif dose_missing_without_reference:
            lines.append(f"- {self.DOSE_MISSING_DISCLAIMER}")

        lines.extend(["", self.DISCLAIMER_1, self.DISCLAIMER_2])
        return "\n".join(lines)

    def _build_patient_report(
        self,
        current_drugs: list[DrugInfo],
        new_drug: DrugInfo,
        patient: PatientInfo,
        risk_summary: RiskSummary,
    ) -> str:
        lines = [
            "用药安全提醒",
            "",
            f"您当前在用：{', '.join(drug.zh_name for drug in current_drugs)}",
            f"计划新增：{new_drug.zh_name}",
            f"综合风险等级：{risk_summary.overall_risk_level}",
            "",
            "需要注意的情况：",
        ]

        if risk_summary.findings:
            for finding in risk_summary.findings:
                lines.append(f"- {finding.title}：{finding.description}。{finding.recommendation}")
        else:
            lines.append("- 当前未在本地规则中发现明确信号，但仍需结合说明书和个人情况确认。")

        if any(finding.evidence_items for finding in risk_summary.findings):
            lines.append("- 以上提醒基于本地用药安全规则和证据摘要生成。")

        if patient.diseases:
            lines.append(f"- 您提供的疾病情况包括：{', '.join(patient.diseases)}，这会影响用药判断。")

        if any(result.dose_source == "label_reference" for result in risk_summary.dose_results):
            lines.append(f"- {self.DOSE_REFERENCE_DISCLAIMER}")
        elif any(result.dose_source == "missing" and result.status == "missing_dose" for result in risk_summary.dose_results):
            lines.append(f"- {self.DOSE_MISSING_DISCLAIMER}")

        lines.extend(
            [
                "",
                "如有症状变化、担心相互影响，建议咨询医生或药师。",
                "",
                self.DISCLAIMER_1,
                self.DISCLAIMER_2,
            ]
        )
        return "\n".join(lines)

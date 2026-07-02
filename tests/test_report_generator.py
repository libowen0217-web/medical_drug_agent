from medical_drug_agent.app.reporting.report_generator import TemplateReportGenerator
from medical_drug_agent.app.schemas import (
    DoseCheckResult,
    DrugInfo,
    PatientInfo,
    RiskFinding,
    RiskSummary,
    RuleMatch,
)


def _summary() -> RiskSummary:
    return RiskSummary(
        overall_risk_level="medium",
        findings=[
            RiskFinding(
                source="rule_match",
                risk_level="medium",
                title="可能影响血压控制",
                description="新增药物布洛芬属于 NSAID，患者存在高血压。",
                mechanism="机制说明",
                recommendation="建议咨询医生或药师。",
                evidence_note="本地规则",
                related_drugs=["硝苯地平", "布洛芬"],
                related_diseases=["高血压"],
            )
        ],
        rule_matches=[RuleMatch("R001", "medium", "可能影响血压控制", "机制说明", "建议咨询医生或药师。", "本地规则", "命中原因")],
        dose_results=[DoseCheckResult("布洛芬", "missing_dose", "unknown", "未提供完整剂量信息", {})],
        kg_relation_count=1,
        notes=[],
    )


def test_generates_pharmacist_report() -> None:
    generator = TemplateReportGenerator()
    pharmacist_report, _ = generator.generate(
        current_drugs=[DrugInfo("硝苯地平", "硝苯地平", "Nifedipine", [], "钙通道阻滞剂/降压药", "")],
        new_drug=DrugInfo("布洛芬", "布洛芬", "Ibuprofen", [], "NSAID/非甾体抗炎药", ""),
        patient=PatientInfo(age=68, diseases=["高血压"]),
        risk_summary=_summary(),
    )
    assert "社区药店用药安全检查报告（药师版）" in pharmacist_report


def test_generates_patient_report() -> None:
    generator = TemplateReportGenerator()
    _, patient_report = generator.generate(
        current_drugs=[DrugInfo("硝苯地平", "硝苯地平", "Nifedipine", [], "钙通道阻滞剂/降压药", "")],
        new_drug=DrugInfo("布洛芬", "布洛芬", "Ibuprofen", [], "NSAID/非甾体抗炎药", ""),
        patient=PatientInfo(age=68, diseases=["高血压"]),
        risk_summary=_summary(),
    )
    assert "用药安全提醒" in patient_report


def test_report_contains_overall_risk_and_disclaimer() -> None:
    generator = TemplateReportGenerator()
    pharmacist_report, patient_report = generator.generate(
        current_drugs=[DrugInfo("硝苯地平", "硝苯地平", "Nifedipine", [], "钙通道阻滞剂/降压药", "")],
        new_drug=DrugInfo("布洛芬", "布洛芬", "Ibuprofen", [], "NSAID/非甾体抗炎药", ""),
        patient=PatientInfo(age=68, diseases=["高血压"]),
        risk_summary=_summary(),
    )
    assert "综合风险等级：medium" in pharmacist_report
    assert "本报告仅为用药安全辅助参考，不构成诊断或处方建议。" in pharmacist_report
    assert "本报告仅为用药安全辅助参考，不构成诊断或处方建议。" in patient_report


def test_report_avoids_forbidden_phrases() -> None:
    generator = TemplateReportGenerator()
    pharmacist_report, patient_report = generator.generate(
        current_drugs=[DrugInfo("硝苯地平", "硝苯地平", "Nifedipine", [], "钙通道阻滞剂/降压药", "")],
        new_drug=DrugInfo("布洛芬", "布洛芬", "Ibuprofen", [], "NSAID/非甾体抗炎药", ""),
        patient=PatientInfo(age=68, diseases=["高血压"]),
        risk_summary=_summary(),
    )
    assert "完全安全" not in pharmacist_report
    assert "可以放心服用" not in patient_report

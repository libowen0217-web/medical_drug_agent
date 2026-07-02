from medical_drug_agent.app.schemas import DoseInput, ReportResult
from medical_drug_agent.app.workflow import DrugSafetyWorkflow


def test_workflow_runs_end_to_end() -> None:
    workflow = DrugSafetyWorkflow()
    result = workflow.run(
        current_drugs=["硝苯地平"],
        new_drug="布洛芬",
        age=68,
        diseases=["高血压"],
    )
    assert isinstance(result, ReportResult)


def test_workflow_returns_non_empty_reports_and_risk_level() -> None:
    workflow = DrugSafetyWorkflow()
    result = workflow.run(
        current_drugs=["硝苯地平"],
        new_drug="布洛芬",
        age=68,
        diseases=["高血压"],
        dose_inputs=[DoseInput(drug_name="布洛芬", single_dose_mg=400, times_per_day=3, duration_days=5)],
    )
    assert result.risk_summary.overall_risk_level
    assert result.pharmacist_report
    assert result.patient_report


def test_reports_do_not_contain_forbidden_phrases_after_filter() -> None:
    workflow = DrugSafetyWorkflow()
    result = workflow.run(
        current_drugs=["硝苯地平"],
        new_drug="布洛芬",
        age=68,
        diseases=["高血压"],
    )
    forbidden = ["你可以吃", "可以吃", "你不能吃", "不能吃", "完全安全", "没有风险", "建议服用"]
    combined = result.pharmacist_report + "\n" + result.patient_report
    assert all(item not in combined for item in forbidden)

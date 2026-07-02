from medical_drug_agent.app.dose.checker import DoseChecker
from medical_drug_agent.app.schemas import DoseInput


def test_ibuprofen_missing_dose_returns_missing_dose() -> None:
    checker = DoseChecker()
    result = checker.check(DoseInput(drug_name="布洛芬"))
    assert result.status == "missing_dose"
    assert result.dose_source == "missing"


def test_ibuprofen_user_input_marks_user_source() -> None:
    checker = DoseChecker()
    result = checker.check(DoseInput(drug_name="布洛芬", single_dose_mg=400, times_per_day=3, duration_days=3))
    assert result.status == "within_reference"
    assert result.dose_source == "user_input"
    assert result.dose_assumption_used is False


def test_ibuprofen_reference_mode_uses_label_reference() -> None:
    checker = DoseChecker()
    result = checker.check(
        DoseInput(
            drug_name="布洛芬",
            dose_mode="label_reference",
            allow_reference_dose=True,
            dose_context="otc_candidate",
        )
    )
    assert result.status == "within_reference"
    assert result.dose_source == "label_reference"
    assert result.dose_source_label == "说明书参考剂量"
    assert result.dose_assumption_used is True
    assert result.dose_confidence == "reference_only"
    assert result.reference_dose == {"single_dose_mg": 200, "times_per_day": 3, "duration_days": 3}
    assert "不代表患者实际用药剂量" in result.message


def test_ibuprofen_600mg_single_dose_returns_exceed_single_dose() -> None:
    checker = DoseChecker()
    result = checker.check(DoseInput(drug_name="布洛芬", single_dose_mg=600, times_per_day=1, duration_days=1))
    assert result.status == "exceed_single_dose"


def test_unknown_drug_returns_unknown_reference() -> None:
    checker = DoseChecker()
    result = checker.check(DoseInput(drug_name="未知药物", single_dose_mg=100, times_per_day=1, duration_days=1))
    assert result.status == "unknown_reference"


def test_acetaminophen_daily_dose_exceeds_reference() -> None:
    checker = DoseChecker()
    result = checker.check(DoseInput(drug_name="对乙酰氨基酚", single_dose_mg=500, times_per_day=7, duration_days=1))
    assert result.status == "exceed_daily_dose"


def test_prescription_drug_without_manual_dose_does_not_assume_reference() -> None:
    checker = DoseChecker()
    result = checker.check(DoseInput(drug_name="硝苯地平"))
    assert result.status == "missing_dose"
    assert result.dose_source == "missing"
    assert result.dose_assumption_used is False

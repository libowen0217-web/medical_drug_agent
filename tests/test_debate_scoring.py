from medical_drug_agent.app.debate.scoring import DebateScorer


def test_symptom_fit_adds_points() -> None:
    assert DebateScorer.symptom_fit_delta("high") == 20


def test_medium_risk_deducts_points() -> None:
    assert DebateScorer.interaction_risk_delta("medium") == -15


def test_high_risk_deducts_more_points() -> None:
    assert DebateScorer.interaction_risk_delta("high") < DebateScorer.interaction_risk_delta("medium")


def test_elderly_ibuprofen_deduction() -> None:
    delta, _, _ = DebateScorer.patient_factor_delta("Ibuprofen", 68, [], [])
    assert delta <= -10


def test_hypertension_ibuprofen_deduction() -> None:
    delta, _, _ = DebateScorer.patient_factor_delta("Ibuprofen", 40, ["高血压"], [])
    assert delta <= -15


def test_liver_dysfunction_acetaminophen_deduction() -> None:
    delta, _, _ = DebateScorer.patient_factor_delta("Acetaminophen", 40, ["肝功能异常"], [])
    assert delta <= -20


def test_high_score_is_preferred_candidate() -> None:
    assert DebateScorer.final_level(70) == "preferred_candidate"


def test_low_score_is_not_preferred() -> None:
    assert DebateScorer.final_level(30) == "not_preferred_without_review"

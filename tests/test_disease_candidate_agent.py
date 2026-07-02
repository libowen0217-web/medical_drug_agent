from medical_drug_agent.app.agents.disease_candidate_agent import DiseaseCandidateAgent
from medical_drug_agent.app.agents.otc_candidate_agent import OTCCandidateAgent


def test_disease_candidate_agent_returns_candidates() -> None:
    state = {
        "input_payload": {"symptom_text": "发热、头痛、咽痛，两天了"},
        "parsed_symptoms": [],
        "red_flags": [],
    }
    result = DiseaseCandidateAgent().run(state)
    assert result.status == "success"
    assert result.output["disease_candidates"]
    assert result.output["referral_required"] is False


def test_disease_candidate_agent_sets_referral_for_lung_cancer() -> None:
    state = {
        "input_payload": {"symptom_text": "肺癌"},
        "parsed_symptoms": [],
        "red_flags": [],
    }
    result = DiseaseCandidateAgent().run(state)
    assert result.status == "success"
    assert result.output["referral_required"] is True
    assert result.output["stop_candidate_recommendation"] is True


def test_otc_candidate_agent_prefers_disease_candidates() -> None:
    disease_result = DiseaseCandidateAgent().run(
        {
            "input_payload": {"symptom_text": "反酸、烧心"},
            "parsed_symptoms": [],
            "red_flags": [],
        }
    )
    state = {
        "input_payload": {"symptom_text": "反酸、烧心"},
        "disease_candidates": disease_result.output["disease_candidates"],
    }
    result = OTCCandidateAgent().run(state)
    assert result.status == "success"
    candidates = result.output["otc_candidates"]
    assert candidates
    assert candidates[0].source == "disease_library"
    assert "奥美拉唑" in candidates[0].candidate_drugs


def test_otc_candidate_agent_skips_when_referral_required() -> None:
    result = OTCCandidateAgent().run({"stop_candidate_recommendation": True})
    assert result.status == "skipped"
    assert result.output["otc_candidates"] == []

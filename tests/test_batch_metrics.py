from medical_drug_agent.app.evaluation.metrics import summarize_batch_result


def test_summarize_counts_and_match_rate() -> None:
    result = {
        "total": 4,
        "success_count": 2,
        "error_count": 2,
        "matched_expected_count": 3,
        "mismatched_expected_count": 1,
        "cases": [
            {"actual_risk_level": "high", "actual_error_code": None},
            {"actual_risk_level": "medium", "actual_error_code": None},
            {"actual_risk_level": None, "actual_error_code": "UNKNOWN_DRUG"},
            {"actual_risk_level": None, "actual_error_code": "INVALID_INPUT"},
        ],
    }

    summary = summarize_batch_result(result)

    assert summary["total"] == 4
    assert summary["success_count"] == 2
    assert summary["error_count"] == 2
    assert summary["risk_level_counts"] == {"high": 1, "medium": 1}
    assert summary["error_code_counts"] == {"UNKNOWN_DRUG": 1, "INVALID_INPUT": 1}
    assert summary["match_rate"] == 0.75

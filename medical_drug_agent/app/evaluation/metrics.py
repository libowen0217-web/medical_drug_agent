from __future__ import annotations

from collections import Counter
from typing import Any


def summarize_batch_result(result: dict[str, Any]) -> dict[str, Any]:
    cases = list(result.get("cases", []) or [])

    risk_level_counts: Counter[str] = Counter()
    error_code_counts: Counter[str] = Counter()

    for case in cases:
        actual_risk_level = case.get("actual_risk_level")
        actual_error_code = case.get("actual_error_code")
        if actual_risk_level:
            risk_level_counts[str(actual_risk_level)] += 1
        if actual_error_code:
            error_code_counts[str(actual_error_code)] += 1

    matched_expected_count = int(result.get("matched_expected_count", 0) or 0)
    mismatched_expected_count = int(result.get("mismatched_expected_count", 0) or 0)
    compared_total = matched_expected_count + mismatched_expected_count
    match_rate = matched_expected_count / compared_total if compared_total else 0.0

    return {
        "total": int(result.get("total", 0) or 0),
        "success_count": int(result.get("success_count", 0) or 0),
        "error_count": int(result.get("error_count", 0) or 0),
        "risk_level_counts": dict(risk_level_counts),
        "error_code_counts": dict(error_code_counts),
        "matched_expected_count": matched_expected_count,
        "mismatched_expected_count": mismatched_expected_count,
        "match_rate": match_rate,
    }

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from medical_drug_agent.app.service import DrugSafetyService


class BatchCaseRunner:
    """Run JSONL drug safety cases through the stable local service interface."""

    CASE_PARSE_ERROR = "CASE_JSON_PARSE_ERROR"
    CASE_RUNTIME_ERROR = "BATCH_CASE_RUNTIME_ERROR"

    def __init__(self, service: DrugSafetyService | None = None) -> None:
        self.service = service or DrugSafetyService()

    def run_cases(self, case_file: Path, enable_audit: bool = False) -> dict[str, Any]:
        case_path = Path(case_file)
        if not case_path.exists():
            raise FileNotFoundError(f"案例文件不存在：{case_path}")

        results: list[dict[str, Any]] = []
        success_count = 0
        error_count = 0
        matched_expected_count = 0
        mismatched_expected_count = 0

        with case_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue

                case_result = self._run_single_line(line, line_number, enable_audit=enable_audit)
                results.append(case_result)

                if case_result["actual_status"] == "success":
                    success_count += 1
                else:
                    error_count += 1

                matched_expected = case_result["matched_expected"]
                if matched_expected is True:
                    matched_expected_count += 1
                elif matched_expected is False:
                    mismatched_expected_count += 1

        return {
            "total": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "matched_expected_count": matched_expected_count,
            "mismatched_expected_count": mismatched_expected_count,
            "cases": results,
        }

    def _run_single_line(
        self,
        line: str,
        line_number: int,
        enable_audit: bool,
    ) -> dict[str, Any]:
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            response = {
                "request_id": "",
                "timestamp": "",
                "status": "error",
                "error_code": self.CASE_PARSE_ERROR,
                "message": f"第 {line_number} 行 JSONL 解析失败：{exc}",
                "data": None,
                "metadata": {"line_number": line_number},
            }
            return {
                "case_id": f"line_{line_number}",
                "case_name": f"未命名案例（第 {line_number} 行）",
                "expected_status": None,
                "expected_error_code": None,
                "expected_risk_level": None,
                "actual_status": "error",
                "actual_error_code": self.CASE_PARSE_ERROR,
                "actual_risk_level": None,
                "matched_expected": None,
                "response": response,
            }

        case_id = str(case.get("case_id", f"line_{line_number}"))
        case_name = str(case.get("case_name", f"未命名案例（第 {line_number} 行）"))
        request = case.get("request", {})

        try:
            response = self.service.check_from_dict(request, enable_audit=enable_audit)
        except Exception as exc:
            response = {
                "request_id": "",
                "timestamp": "",
                "status": "error",
                "error_code": self.CASE_RUNTIME_ERROR,
                "message": f"案例运行失败：{exc}",
                "data": None,
                "metadata": {"line_number": line_number},
            }

        actual_status = response.get("status")
        actual_error_code = response.get("error_code")
        actual_risk_level = (response.get("data") or {}).get("overall_risk_level")
        matched_expected = self._match_expected(case, response)

        return {
            "case_id": case_id,
            "case_name": case_name,
            "expected_status": case.get("expected_status"),
            "expected_error_code": case.get("expected_error_code"),
            "expected_risk_level": case.get("expected_risk_level"),
            "actual_status": actual_status,
            "actual_error_code": actual_error_code,
            "actual_risk_level": actual_risk_level,
            "matched_expected": matched_expected,
            "response": response,
        }

    @staticmethod
    def _match_expected(case: dict[str, Any], response: dict[str, Any]) -> bool | None:
        has_expected = any(
            key in case for key in ("expected_status", "expected_error_code", "expected_risk_level")
        )
        if not has_expected:
            return None

        checks: list[bool] = []

        if "expected_status" in case:
            checks.append(response.get("status") == case.get("expected_status"))

        if "expected_error_code" in case:
            checks.append(response.get("error_code") == case.get("expected_error_code"))

        if "expected_risk_level" in case:
            checks.append(
                response.get("status") == "success"
                and (response.get("data") or {}).get("overall_risk_level")
                == case.get("expected_risk_level")
            )

        return all(checks)

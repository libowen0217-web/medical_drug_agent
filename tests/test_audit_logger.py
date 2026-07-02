from pathlib import Path

from medical_drug_agent.app.audit.logger import AuditLogger


def _request_payload() -> dict:
    return {
        "current_drugs": ["硝苯地平"],
        "new_drug": "布洛芬",
        "age": 68,
        "diseases": ["高血压"],
        "patient_factors": [],
        "dose": None,
    }


def _response_payload() -> dict:
    return {
        "request_id": "req-1",
        "timestamp": "2026-06-16T00:00:00+00:00",
        "status": "success",
        "error_code": None,
        "message": "检查完成",
        "data": {
            "overall_risk_level": "medium",
            "risk_findings": [1, 2],
            "pharmacist_report": "x",
            "patient_report": "y",
            "safety_warnings": [],
        },
        "metadata": {
            "engine_version": "local-csv-mvp-v1",
            "risk_finding_count": 2,
            "safety_warning_count": 0,
        },
    }


def test_logger_can_write_record(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    result = logger.log_case(_request_payload(), _response_payload())
    assert result["logged"] is True


def test_jsonl_file_exists_after_write(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path)
    logger.log_case(_request_payload(), _response_payload())
    assert log_path.exists()


def test_load_all_reads_logs(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    logger.log_case(_request_payload(), _response_payload())
    records = logger.load_all()
    assert len(records) == 1


def test_find_by_audit_id_and_request_id(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    result = logger.log_case(_request_payload(), _response_payload())
    record_by_audit = logger.find_by_audit_id(result["audit_id"])
    record_by_request = logger.find_by_request_id("req-1")
    assert record_by_audit is not None
    assert record_by_request is not None


def test_record_contains_required_fields(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    logger.log_case(_request_payload(), _response_payload())
    record = logger.load_all()[0]
    for key in ["audit_id", "request_id", "request", "response_summary", "response"]:
        assert key in record


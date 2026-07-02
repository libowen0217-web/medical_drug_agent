from pathlib import Path

from medical_drug_agent.app.audit.logger import AuditLogger
from medical_drug_agent.app.audit.replay import AuditReplayer
from medical_drug_agent.app.service import DrugSafetyService


def _payload() -> dict:
    return {
        "current_drugs": ["硝苯地平"],
        "new_drug": "布洛芬",
        "age": 68,
        "diseases": ["高血压"],
        "patient_factors": [],
        "dose": None,
    }


def test_replay_by_audit_id_success(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path)
    service = DrugSafetyService(audit_logger=logger)
    response = service.check_from_dict(_payload(), enable_audit=True)
    audit_id = response["metadata"]["audit"]["audit_id"]

    replayer = AuditReplayer(logger=logger, service=service)
    replay = replayer.replay_by_audit_id(audit_id)
    assert replay["status"] == "success"


def test_replay_contains_request_ids(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path)
    service = DrugSafetyService(audit_logger=logger)
    response = service.check_from_dict(_payload(), enable_audit=True)
    audit_id = response["metadata"]["audit"]["audit_id"]

    replayer = AuditReplayer(logger=logger, service=service)
    replay = replayer.replay_by_audit_id(audit_id)
    assert replay["original_request_id"]
    assert replay["new_request_id"]


def test_same_overall_risk_level_is_boolean(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path)
    service = DrugSafetyService(audit_logger=logger)
    response = service.check_from_dict(_payload(), enable_audit=True)
    audit_id = response["metadata"]["audit"]["audit_id"]

    replayer = AuditReplayer(logger=logger, service=service)
    replay = replayer.replay_by_audit_id(audit_id)
    assert isinstance(replay["same_overall_risk_level"], bool)


def test_replay_missing_audit_id_returns_error(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    replayer = AuditReplayer(logger=logger, service=DrugSafetyService(audit_logger=logger))
    replay = replayer.replay_by_audit_id("missing-id")
    assert replay["status"] == "error"

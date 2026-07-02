from __future__ import annotations

from medical_drug_agent.app.audit.logger import AuditLogger
from medical_drug_agent.app.service import DrugSafetyService


class AuditReplayer:
    """Replay historical audit records through the current service implementation."""

    def __init__(
        self,
        logger: AuditLogger | None = None,
        service: DrugSafetyService | None = None,
    ) -> None:
        self.logger = logger or AuditLogger()
        self.service = service or DrugSafetyService()

    def replay_by_audit_id(self, audit_id: str) -> dict:
        record = self.logger.find_by_audit_id(audit_id)
        if record is None:
            return {"status": "error", "message": "未找到对应审计记录"}
        return self._replay_record(record)

    def replay_by_request_id(self, request_id: str) -> dict:
        record = self.logger.find_by_request_id(request_id)
        if record is None:
            return {"status": "error", "message": "未找到对应审计记录"}
        return self._replay_record(record)

    def _replay_record(self, record: dict) -> dict:
        original_request = dict(record.get("request", {}) or {})
        new_response = self.service.check_from_dict(original_request, enable_audit=False)
        original_response = record.get("response", {}) or {}
        original_data = original_response.get("data") or {}
        new_data = new_response.get("data") or {}
        return {
            "status": "success",
            "audit_id": record.get("audit_id", ""),
            "original_request_id": record.get("request_id", ""),
            "new_request_id": new_response.get("request_id", ""),
            "same_overall_risk_level": original_data.get("overall_risk_level") == new_data.get("overall_risk_level"),
            "same_status": original_response.get("status") == new_response.get("status"),
            "original_summary": record.get("response_summary", {}),
            "new_summary": {
                "status": new_response.get("status"),
                "error_code": new_response.get("error_code"),
                "overall_risk_level": new_data.get("overall_risk_level"),
                "risk_finding_count": (new_response.get("metadata") or {}).get("risk_finding_count", 0),
                "safety_warning_count": (new_response.get("metadata") or {}).get("safety_warning_count", 0),
            },
            "new_response": new_response,
        }


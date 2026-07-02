from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class AuditLogger:
    """Write and read JSONL-based local audit logs."""

    def __init__(self, log_path: Path | None = None) -> None:
        self.log_path = log_path or Path("logs") / "audit" / "drug_safety_audit.jsonl"

    def log_case(self, request_payload: dict, response_payload: dict) -> dict:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            audit_id = str(uuid4())
            record = {
                "audit_id": audit_id,
                "request_id": response_payload.get("request_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "engine_version": response_payload.get("metadata", {}).get("engine_version", "local-csv-mvp-v1"),
                "request": self._sanitize_request(request_payload),
                "response_summary": self._build_response_summary(response_payload),
                "response": response_payload,
            }
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            return {
                "logged": True,
                "audit_id": audit_id,
                "log_path": str(self.log_path),
            }
        except Exception as exc:
            return {
                "logged": False,
                "error": str(exc),
            }

    def load_all(self, limit: int | None = None) -> list[dict]:
        if not self.log_path.exists():
            return []
        records: list[dict] = []
        with self.log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        if limit is not None:
            return records[-limit:]
        return records

    def find_by_request_id(self, request_id: str) -> dict | None:
        for record in reversed(self.load_all()):
            if record.get("request_id") == request_id:
                return record
        return None

    def find_by_audit_id(self, audit_id: str) -> dict | None:
        for record in reversed(self.load_all()):
            if record.get("audit_id") == audit_id:
                return record
        return None

    @staticmethod
    def _sanitize_request(payload: dict) -> dict:
        return {
            "current_drugs": list(payload.get("current_drugs", []) or []),
            "new_drug": payload.get("new_drug", ""),
            "age": payload.get("age"),
            "diseases": list(payload.get("diseases", []) or []),
            "patient_factors": list(payload.get("patient_factors", []) or []),
            "dose": payload.get("dose"),
            "has_dose": payload.get("dose") is not None,
        }

    @staticmethod
    def _build_response_summary(response_payload: dict) -> dict:
        data = response_payload.get("data") or {}
        metadata = response_payload.get("metadata") or {}
        return {
            "status": response_payload.get("status"),
            "error_code": response_payload.get("error_code"),
            "overall_risk_level": data.get("overall_risk_level"),
            "risk_finding_count": metadata.get("risk_finding_count", 0),
            "safety_warning_count": metadata.get("safety_warning_count", 0),
        }


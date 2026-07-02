from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def _build_base_response(status: str, error_code: str | None, message: str) -> dict:
    return {
        "request_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "error_code": error_code,
        "message": message,
    }


def build_success_response(data: dict, metadata: dict, message: str = "检查完成") -> dict:
    response = _build_base_response(status="success", error_code=None, message=message)
    response["data"] = data
    response["metadata"] = metadata
    return response


def build_error_response(
    error_code: str,
    message: str,
    metadata: dict | None = None,
) -> dict:
    response = _build_base_response(status="error", error_code=error_code, message=message)
    response["data"] = None
    response["metadata"] = metadata or {}
    return response

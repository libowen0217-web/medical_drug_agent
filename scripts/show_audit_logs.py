from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.audit.logger import AuditLogger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show recent audit logs.")
    parser.add_argument("--limit", type=int, default=10)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logger = AuditLogger()
    records = logger.load_all(limit=args.limit)
    for record in records:
        request = record.get("request", {})
        summary = record.get("response_summary", {})
        print(
            f"audit_id={record.get('audit_id')} "
            f"request_id={record.get('request_id')} "
            f"timestamp={record.get('timestamp')} "
            f"status={summary.get('status')} "
            f"overall_risk_level={summary.get('overall_risk_level')} "
            f"current_drugs={request.get('current_drugs')} "
            f"new_drug={request.get('new_drug')} "
            f"diseases={request.get('diseases')}"
        )


if __name__ == "__main__":
    main()


from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.audit.replay import AuditReplayer
from medical_drug_agent.app.serialization import to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay an audit log entry.")
    parser.add_argument("--audit-id")
    parser.add_argument("--request-id")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    replayer = AuditReplayer()
    if args.audit_id:
        result = replayer.replay_by_audit_id(args.audit_id)
    elif args.request_id:
        result = replayer.replay_by_request_id(args.request_id)
    else:
        print("请提供 --audit-id 或 --request-id")
        raise SystemExit(1)

    if result.get("status") == "error":
        print(result.get("message"))
        raise SystemExit(1)

    print(f"original_request_id: {result.get('original_request_id')}")
    print(f"new_request_id: {result.get('new_request_id')}")
    print(f"original_overall_risk_level: {result.get('original_summary', {}).get('overall_risk_level')}")
    print(f"new_overall_risk_level: {result.get('new_summary', {}).get('overall_risk_level')}")
    print(f"same_overall_risk_level: {result.get('same_overall_risk_level')}")
    print(f"same_status: {result.get('same_status')}")
    print(to_json(result.get("new_response")))


if __name__ == "__main__":
    main()


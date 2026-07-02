from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.serialization import to_json
from medical_drug_agent.app.service import DrugSafetyService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a drug safety case through the LangGraph workflow.")
    parser.add_argument("--input", help="Optional input JSON file path.")
    return parser


def _default_payload() -> dict:
    return {
        "current_drugs": ["硝苯地平"],
        "new_drug": "布洛芬",
        "age": 68,
        "diseases": ["高血压"],
        "patient_factors": [],
        "dose": None,
    }


def main() -> int:
    args = build_parser().parse_args()
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(to_json({"status": "error", "message": f"输入文件不存在：{input_path}"}))
            return 1
        try:
            payload = json.loads(input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(to_json({"status": "error", "message": f"JSON 格式错误：{exc}"}))
            return 1
    else:
        payload = _default_payload()

    service = DrugSafetyService(use_graph=True)
    response = service.check_from_dict(payload)
    print(to_json(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

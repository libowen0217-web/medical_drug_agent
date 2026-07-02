from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.api_contract import build_error_response
from medical_drug_agent.app.serialization import to_json
from medical_drug_agent.app.service import DrugSafetyService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a drug safety JSON case through the local service.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file.")
    parser.add_argument("--output", help="Optional path to save the output JSON.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        response = build_error_response(
            error_code="INVALID_INPUT",
            message=f"输入文件不存在：{input_path}",
            metadata={"engine_version": DrugSafetyService.ENGINE_VERSION},
        )
        print(to_json(response))
        raise SystemExit(1)

    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        response = build_error_response(
            error_code="JSON_PARSE_ERROR",
            message=f"JSON 格式错误：{exc}",
            metadata={"engine_version": DrugSafetyService.ENGINE_VERSION},
        )
        print(to_json(response))
        raise SystemExit(1)

    service = DrugSafetyService()
    response = service.check_from_dict(payload)
    response_json = to_json(response)
    print(response_json)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(response_json, encoding="utf-8")


if __name__ == "__main__":
    main()

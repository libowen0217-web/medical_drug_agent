from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medical_drug_agent.app.serialization import to_json
from medical_drug_agent.app.symptom.symptom_workflow import SymptomConsultWorkflow


DEFAULT_PAYLOAD = {
    "symptom_text": "发热、头痛、嗓子疼，两天了",
    "age": 68,
    "sex": "unknown",
    "temperature_c": 38.5,
    "duration_days": 2,
    "current_drugs": ["硝苯地平"],
    "diseases": ["高血压"],
    "patient_factors": [],
    "allergies": [],
}

RED_FLAG_PAYLOAD = {
    "symptom_text": "发烧40度，胸痛，呼吸困难，意识有点模糊",
    "age": 70,
    "sex": "unknown",
    "temperature_c": 40.0,
    "duration_days": 1,
    "current_drugs": ["硝苯地平"],
    "diseases": ["高血压"],
    "patient_factors": ["老年人"],
    "allergies": [],
}


def load_payload(input_path: Path | None, red_flag_demo: bool) -> dict:
    if red_flag_demo:
        return dict(RED_FLAG_PAYLOAD)
    if input_path is None:
        return dict(DEFAULT_PAYLOAD)
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{input_path}")
    try:
        return json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"输入 JSON 格式错误：{exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the symptom consult workflow.")
    parser.add_argument("--input", type=Path, help="Optional JSON input file path.")
    parser.add_argument("--red-flag-demo", action="store_true", help="Run the red flag demo payload.")
    args = parser.parse_args()

    try:
        payload = load_payload(args.input, args.red_flag_demo)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc))
        return 1

    response = SymptomConsultWorkflow().run(payload)
    data = response.get("data") or {}
    metadata = response.get("metadata") or {}
    print(f"status: {response.get('status')}")
    print(f"error_code: {response.get('error_code')}")
    print(f"red_flag_triggered: {metadata.get('red_flag_triggered')}")
    print(f"otc_candidate_count: {len(data.get('otc_candidates', []) or [])}")
    print(f"candidate_safety_count: {len(data.get('candidate_safety_results', []) or [])}")
    print("consult_report:")
    print(data.get("consult_report", ""))
    print("full_json:")
    print(to_json(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from medical_drug_agent.app.agents.supervisor_agent import SupervisorAgent
from medical_drug_agent.app.serialization import to_json


DEFAULT_PAYLOAD = {
    "current_drugs": ["硝苯地平"],
    "new_drug": "布洛芬",
    "age": 68,
    "diseases": ["高血压"],
    "patient_factors": [],
    "dose": None,
}


def load_payload(input_path: Path | None) -> dict:
    if input_path is None:
        return dict(DEFAULT_PAYLOAD)
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{input_path}")
    try:
        return json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"输入 JSON 格式错误：{exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the multi-agent local drug safety workflow.")
    parser.add_argument("--input", type=Path, help="Optional JSON input file path.")
    parser.add_argument("--enable-audit", action="store_true", help="Enable audit logging.")
    parser.add_argument("--enable-llm", dest="enable_llm", action="store_true", help="Enable LLM report polishing.")
    parser.add_argument("--disable-llm", dest="enable_llm", action="store_false", help="Disable LLM report polishing.")
    parser.add_argument(
        "--knowledge-backend",
        choices=["auto", "csv", "neo4j"],
        default=None,
        help="Override the knowledge query backend.",
    )
    parser.set_defaults(enable_llm=True)
    args = parser.parse_args()

    try:
        payload = load_payload(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc))
        return 1

    supervisor = SupervisorAgent(
        enable_audit=args.enable_audit,
        enable_llm=args.enable_llm,
        knowledge_backend=args.knowledge_backend,
    )
    response = supervisor.run(payload)
    data = response.get("data") or {}
    metadata = response.get("metadata") or {}
    multi_agent = metadata.get("multi_agent") or {}

    print(f"status: {response.get('status')}")
    print(f"error_code: {response.get('error_code')}")
    print(f"overall_risk_level: {data.get('overall_risk_level')}")
    print(f"llm_enabled: {multi_agent.get('llm_enabled')}")
    print(f"llm_used: {multi_agent.get('llm_used')}")
    print(f"llm_error: {multi_agent.get('llm_error')}")
    print(f"configured_knowledge_backend: {metadata.get('configured_knowledge_backend')}")
    print(f"active_knowledge_backend: {metadata.get('active_knowledge_backend')}")
    print(f"knowledge_backend: {metadata.get('knowledge_backend')}")
    print(f"fallback_used: {metadata.get('fallback_used')}")
    print(f"fallback_reason: {metadata.get('fallback_reason')}")
    print(f"agents_executed: {multi_agent.get('agents_executed')}")
    print(f"agents_failed: {multi_agent.get('agents_failed')}")
    print("pharmacist_report:")
    print(data.get("pharmacist_report", ""))
    print("patient_report:")
    print(data.get("patient_report", ""))
    print("full_json:")
    print(to_json(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

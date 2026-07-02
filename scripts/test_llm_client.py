from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from medical_drug_agent.app.llm.client import LLMClient


SYSTEM_PROMPT = "你是一个报告润色助手。"
USER_PROMPT = (
    '请只返回 JSON：'
    '{"pharmacist_report":"测试药师报告","patient_report":"测试患者报告"}'
)


def main() -> int:
    try:
        client = LLMClient()
    except Exception as exc:
        print("success: false")
        print(f"error: {exc}")
        return 1

    print(f"provider: {client.provider}")
    print(f"base_url: {client.base_url}")
    print(f"model: {client.model}")

    try:
        text = client.generate_text(SYSTEM_PROMPT, USER_PROMPT)
        preview = str(text or "")[:500]
        print("success: true")
        print(f"response_preview: {preview}")
        return 0
    except Exception as exc:
        print("success: false")
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

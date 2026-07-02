from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from medical_drug_agent.app.agents import LLMReportAgent
from medical_drug_agent.app.llm.client import (
    LLMClient,
    build_anthropic_messages_url,
    extract_anthropic_text,
    resolve_provider,
)
from medical_drug_agent.app.schemas import DrugInfo, EvidenceItem, PatientInfo, RiskFinding, RiskSummary


class MockLLMClient:
    def __init__(
        self,
        text: str = "",
        error: Exception | None = None,
        model: str = "mock-model",
        provider: str = "openai",
    ) -> None:
        self.text = text
        self.error = error
        self.model = model
        self.provider = provider

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        if self.error is not None:
            raise self.error
        return self.text


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text or str(self._payload)

    def json(self) -> dict:
        return self._payload


class FakeClient:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict] = []

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, headers: dict, json: dict) -> FakeResponse:
        self.calls.append({"url": url, "headers": headers, "json": json})
        return self.response


def _state() -> dict:
    finding = RiskFinding(
        source="rule_match",
        risk_level="medium",
        title="可能影响血压控制",
        description="布洛芬可能影响高血压患者血压控制",
        mechanism="NSAID 相关机制",
        recommendation="建议监测血压",
        evidence_note="本地规则",
        related_drugs=["硝苯地平", "布洛芬"],
        evidence_items=[
            EvidenceItem(
                evidence_id="EV001",
                topic="NSAID高血压风险",
                source_type="local_label_summary",
                source_name="本地摘要",
                evidence_text="说明书摘要",
                matched_reason="命中",
            )
        ],
    )
    return {
        "normalized_current_drugs": [DrugInfo("硝苯地平", "硝苯地平", "Nifedipine", [], "降压药", "")],
        "normalized_new_drug": DrugInfo("布洛芬", "布洛芬", "Ibuprofen", [], "NSAID", ""),
        "patient_info": PatientInfo(age=68, diseases=["高血压"], patient_factors=[]),
        "risk_summary": RiskSummary(overall_risk_level="medium", findings=[finding]),
        "pharmacist_report": "原始药师报告\n\n本报告仅为用药安全辅助参考，不构成诊断或处方建议。",
        "patient_report": "原始患者报告\n\n本报告仅为用药安全辅助参考，不构成诊断或处方建议。",
    }


def test_resolve_provider_openai() -> None:
    assert resolve_provider("openai", "https://example.com/v1") == "openai"


def test_resolve_provider_anthropic() -> None:
    assert resolve_provider("anthropic", "https://example.com/anthropic") == "anthropic"


def test_resolve_provider_auto_for_anthropic_url() -> None:
    assert resolve_provider("auto", "https://xxx/anthropic") == "anthropic"


def test_resolve_provider_auto_for_openai_url() -> None:
    assert resolve_provider("auto", "https://xxx/v1") == "openai"


def test_build_anthropic_messages_url_from_base_path() -> None:
    assert (
        build_anthropic_messages_url("https://token-plan-cn.xiaomimimo.com/anthropic")
        == "https://token-plan-cn.xiaomimimo.com/anthropic/v1/messages"
    )


def test_build_anthropic_messages_url_from_v1_path() -> None:
    assert (
        build_anthropic_messages_url("https://xxx/anthropic/v1")
        == "https://xxx/anthropic/v1/messages"
    )


def test_extract_anthropic_text_parses_standard_content() -> None:
    assert (
        extract_anthropic_text(
            {
                "content": [
                    {"type": "text", "text": "第一段"},
                    {"type": "text", "text": "第二段"},
                ]
            }
        )
        == "第一段\n第二段"
    )


def test_extract_anthropic_text_accepts_string_content() -> None:
    assert extract_anthropic_text({"content": "直接文本"}) == "直接文本"


def test_extract_anthropic_text_accepts_completion() -> None:
    assert extract_anthropic_text({"completion": "完成文本"}) == "完成文本"


def test_extract_anthropic_text_accepts_message_content() -> None:
    assert extract_anthropic_text({"message": {"content": "消息文本"}}) == "消息文本"


def test_extract_anthropic_text_accepts_openai_like_choices() -> None:
    assert (
        extract_anthropic_text({"choices": [{"message": {"content": "choices文本"}}]})
        == "choices文本"
    )


def test_extract_anthropic_text_raises_service_error() -> None:
    with pytest.raises(ValueError, match="Anthropic 服务返回错误：bad request"):
        extract_anthropic_text({"type": "error", "error": {"message": "bad request"}})


def test_extract_anthropic_text_raises_with_response_keys() -> None:
    with pytest.raises(ValueError, match="response_keys"):
        extract_anthropic_text({"id": "abc", "model": "demo"})


def test_anthropic_http_error_raises_clear_exception() -> None:
    fake = FakeClient(FakeResponse(400, {"error": "bad request"}, text='{"error":"bad request"}'))
    with patch.object(httpx, "Client", lambda *args, **kwargs: fake):
        client = LLMClient(
            api_key="test-key",
            base_url="https://token-plan-cn.xiaomimimo.com/anthropic",
            model="test-model",
            provider="anthropic",
        )

        with pytest.raises(ValueError, match="Anthropic HTTP 调用失败：status=400"):
            client.generate_text("system", "user")


def test_openai_compatible_mock_still_works() -> None:
    fake = FakeClient(
        FakeResponse(
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"pharmacist_report":"润色药师报告","patient_report":"润色患者报告"}'
                        }
                    }
                ]
            },
        )
    )
    with patch.object(httpx, "Client", lambda *args, **kwargs: fake):
        client = LLMClient(
            api_key="test-key",
            base_url="https://token-plan-cn.xiaomimimo.com/v1",
            model="test-model",
            provider="openai",
        )

        text = client.generate_text("system", "user")

        assert "润色药师报告" in text
        assert fake.calls[0]["url"] == "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"


def test_anthropic_request_disables_thinking() -> None:
    fake = FakeClient(
        FakeResponse(
            200,
            {
                "content": [
                    {
                        "type": "text",
                        "text": '{"pharmacist_report":"润色药师报告","patient_report":"润色患者报告"}',
                    }
                ]
            },
        )
    )
    with patch.object(httpx, "Client", lambda *args, **kwargs: fake):
        client = LLMClient(
            api_key="test-key",
            base_url="https://token-plan-cn.xiaomimimo.com/anthropic",
            model="test-model",
            provider="anthropic",
        )

        text = client.generate_text("system", "user")

        assert "润色药师报告" in text
        assert fake.calls[0]["json"]["thinking"] == {"type": "disabled"}


def test_enable_llm_false_returns_skipped() -> None:
    result = LLMReportAgent(enable_llm=False).run(_state())
    assert result.status == "skipped"


def test_enable_llm_true_replaces_reports_when_json_valid() -> None:
    client = MockLLMClient('{"pharmacist_report":"润色药师报告","patient_report":"润色患者报告"}')
    result = LLMReportAgent(enable_llm=True, client=client).run(_state())
    assert result.status == "success"
    assert result.output["pharmacist_report"] == "润色药师报告"
    assert result.output["patient_report"] == "润色患者报告"


def test_invalid_json_falls_back_to_template_reports() -> None:
    result = LLMReportAgent(enable_llm=True, client=MockLLMClient("not-json")).run(_state())
    assert result.status == "success"
    assert result.output["pharmacist_report"].startswith("原始药师报告")
    assert result.output["llm_metadata"]["llm_used"] is False


def test_llm_exception_falls_back_to_template_reports() -> None:
    result = LLMReportAgent(enable_llm=True, client=MockLLMClient(error=RuntimeError("boom"))).run(_state())
    assert result.status == "success"
    assert result.output["patient_report"].startswith("原始患者报告")
    assert result.output["llm_metadata"]["llm_used"] is False


def test_llm_cannot_modify_risk_findings() -> None:
    state = _state()
    result = LLMReportAgent(
        enable_llm=True,
        client=MockLLMClient('{"pharmacist_report":"润色药师报告","patient_report":"润色患者报告","risk_findings":[{"x":1}]}'),
    ).run(state)
    assert result.output["pharmacist_report"] == "润色药师报告"
    assert state["risk_summary"].findings[0].title == "可能影响血压控制"


def test_llm_cannot_modify_overall_risk_level() -> None:
    state = _state()
    result = LLMReportAgent(
        enable_llm=True,
        client=MockLLMClient('{"pharmacist_report":"润色药师报告","patient_report":"润色患者报告","overall_risk_level":"low"}'),
    ).run(state)
    assert result.output["llm_metadata"]["llm_used"] is True
    assert state["risk_summary"].overall_risk_level == "medium"


def test_metadata_records_llm_status() -> None:
    result = LLMReportAgent(
        enable_llm=True,
        client=MockLLMClient(
            '{"pharmacist_report":"润色药师报告","patient_report":"润色患者报告"}',
            model="mock-provider-model",
            provider="openai",
        ),
    ).run(_state())
    metadata = result.output["llm_metadata"]
    assert metadata["llm_enabled"] is True
    assert metadata["llm_used"] is True
    assert metadata["llm_provider"] == "openai"
    assert metadata["llm_error"] is None


def test_metadata_records_anthropic_provider() -> None:
    result = LLMReportAgent(
        enable_llm=True,
        client=MockLLMClient(
            '{"pharmacist_report":"润色药师报告","patient_report":"润色患者报告"}',
            model="claude-compatible-model",
            provider="anthropic",
        ),
    ).run(_state())
    metadata = result.output["llm_metadata"]
    assert metadata["llm_used"] is True
    assert metadata["llm_provider"] == "anthropic"

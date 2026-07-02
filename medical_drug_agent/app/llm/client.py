from __future__ import annotations

import json
import os

import httpx
from dotenv import load_dotenv


load_dotenv()

SUPPORTED_PROVIDERS = {"openai", "anthropic", "auto"}
DEBUG_BODY_LIMIT = 1000


def resolve_provider(provider: str | None, base_url: str) -> str:
    resolved = (provider or os.getenv("LLM_PROVIDER") or "auto").strip().lower()
    if resolved not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"不支持的 LLM_PROVIDER: {resolved}，仅支持 openai、anthropic、auto"
        )

    if resolved == "auto":
        if "anthropic" in str(base_url or "").lower():
            return "anthropic"
        return "openai"
    return resolved


def build_openai_chat_completions_url(base_url: str) -> str:
    normalized = str(base_url or "").rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def build_anthropic_messages_url(base_url: str) -> str:
    normalized = str(base_url or "").rstrip("/")
    if normalized.endswith("/v1/messages"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/messages"
    return f"{normalized}/v1/messages"


def extract_anthropic_text(data: dict) -> str:
    if not isinstance(data, dict):
        raise ValueError("Anthropic 响应结构无效，顶层不是对象")

    error_payload = data.get("error")
    if data.get("type") == "error" and isinstance(error_payload, dict):
        error_message = str(error_payload.get("message") or "未知错误").strip()
        raise ValueError(f"Anthropic 服务返回错误：{error_message}")
    if isinstance(error_payload, dict):
        error_message = str(error_payload.get("message") or "未知错误").strip()
        raise ValueError(f"Anthropic 服务返回错误：{error_message}")

    content = data.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
            elif isinstance(item, str) and item.strip():
                parts.append(item.strip())
        merged = "\n".join(parts).strip()
        if merged:
            return merged

    completion = data.get("completion")
    if isinstance(completion, str) and completion.strip():
        return completion.strip()

    message = data.get("message")
    if isinstance(message, dict):
        message_content = message.get("content")
        if isinstance(message_content, str) and message_content.strip():
            return message_content.strip()
        if isinstance(message_content, list):
            parts = []
            for item in message_content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
                elif isinstance(item, str) and item.strip():
                    parts.append(item.strip())
            merged = "\n".join(parts).strip()
            if merged:
                return merged

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            choice_message = first.get("message")
            if isinstance(choice_message, dict):
                choice_content = choice_message.get("content")
                if isinstance(choice_content, str) and choice_content.strip():
                    return choice_content.strip()

    response_keys = sorted(data.keys())
    raise ValueError(
        f"Anthropic 响应中没有可解析的文本内容，response_keys={response_keys}"
    )


class LLMClient:
    """Unified LLM client supporting OpenAI-compatible and Anthropic-compatible APIs."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        provider: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = str(base_url or os.getenv("LLM_BASE_URL") or "").strip()
        self.model = str(model or os.getenv("LLM_MODEL") or "").strip()
        self.provider = resolve_provider(provider, self.base_url)
        self.debug_enabled = self._is_debug_enabled()
        self._validate_config()

    def _validate_config(self) -> None:
        if not self.api_key:
            raise ValueError("未配置 LLM_API_KEY，无法启用 LLMReportAgent")
        if not self.base_url:
            raise ValueError("未配置 LLM_BASE_URL，无法启用 LLMReportAgent")
        if not self.model:
            raise ValueError("未配置 LLM_MODEL，无法启用 LLMReportAgent")

    @staticmethod
    def _is_debug_enabled() -> bool:
        value = str(os.getenv("LLM_DEBUG") or "false").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _debug_log_response(self, url: str, response: httpx.Response) -> None:
        if not self.debug_enabled:
            return

        print(f"[LLM DEBUG] provider={self.provider}")
        print(f"[LLM DEBUG] url={url}")
        print(f"[LLM DEBUG] model={self.model}")
        print(f"[LLM DEBUG] status_code={response.status_code}")

        parsed_json: dict | None = None
        try:
            payload = response.json()
            if isinstance(payload, dict):
                parsed_json = payload
                print(f"[LLM DEBUG] response_keys={sorted(payload.keys())}")
            else:
                print(f"[LLM DEBUG] response_type={type(payload).__name__}")
        except Exception:
            parsed_json = None

        if parsed_json is not None:
            preview = json.dumps(parsed_json, ensure_ascii=False)[:DEBUG_BODY_LIMIT]
            print(f"[LLM DEBUG] response_preview={preview}")
        else:
            print(f"[LLM DEBUG] response_preview={response.text[:DEBUG_BODY_LIMIT]}")

    @staticmethod
    def _safe_response_body(response: httpx.Response) -> str:
        text = (response.text or "")[:DEBUG_BODY_LIMIT]
        return text.replace("\n", " ").replace("\r", " ")

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "anthropic":
            return self._generate_anthropic_text(system_prompt, user_prompt)
        return self._generate_openai_text(system_prompt, user_prompt)

    def _generate_openai_text(self, system_prompt: str, user_prompt: str) -> str:
        url = build_openai_chat_completions_url(self.base_url)
        with httpx.Client(timeout=60.0, trust_env=False) as client:
            response = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                },
            )

        self._debug_log_response(url, response)

        if response.status_code < 200 or response.status_code >= 300:
            raise ValueError(
                f"OpenAI-compatible HTTP 调用失败：status={response.status_code}, "
                f"url={url}, body={self._safe_response_body(response)}"
            )

        body = response.json()
        try:
            return str(body["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                f"OpenAI-compatible 响应结构无效，缺少 message.content，url={url}"
            ) from exc

    def _generate_anthropic_text(self, system_prompt: str, user_prompt: str) -> str:
        url = build_anthropic_messages_url(self.base_url)
        with httpx.Client(timeout=60.0, trust_env=False) as client:
            response = client.post(
                url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1200,
                    "temperature": 0.2,
                    "system": system_prompt,
                    "thinking": {"type": "disabled"},
                    "messages": [
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                    ],
                },
            )

        self._debug_log_response(url, response)

        if response.status_code < 200 or response.status_code >= 300:
            raise ValueError(
                f"Anthropic HTTP 调用失败：status={response.status_code}, "
                f"url={url}, body={self._safe_response_body(response)}"
            )

        try:
            body = response.json()
        except Exception as exc:
            raise ValueError(
                f"Anthropic 响应不是合法 JSON，url={url}, body={self._safe_response_body(response)}"
            ) from exc

        return extract_anthropic_text(body)

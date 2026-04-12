from __future__ import annotations

import json
import re
from typing import Any
from urllib import error, request

from ..config import Settings
from .types import ModelResponse


class LocalOpenAIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        require_json: bool,
        temperature: float = 0.0,
    ) -> ModelResponse:
        if not self.settings.local_ready():
            raise RuntimeError(
                "LLAMACPP_BASE_URL or LLAMACPP_MODEL is missing. "
                "Put the Colab export block in .env.colab or set the variables in your shell."
            )

        payload = {
            "model": self.settings.llamacpp_model,
            "messages": self._prepare_messages(messages, require_json=require_json),
            "temperature": temperature,
            "max_tokens": self.settings.local_max_tokens,
        }
        if require_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            data = self._send_with_context_window_retries(payload)
        except (error.URLError, OSError) as exc:
            raise RuntimeError(
                "Could not reach local OpenAI-compatible server at "
                f"{self.settings.llamacpp_chat_url}: {getattr(exc, 'reason', exc)}. "
                "This stage only uses the Colab-hosted local model path."
            ) from exc

        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected local model response: {data}") from exc

        return ModelResponse(
            content=self._coerce_content(message.get("content", "")),
            reasoning_details=message.get("reasoning_details"),
            raw_response=data,
            model=str(message.get("model") or self.settings.llamacpp_model),
        )

    def _send_with_context_window_retries(self, payload: dict[str, Any]) -> dict[str, Any]:
        current_payload = dict(payload)
        for _ in range(12):
            try:
                return self._send_request(current_payload)
            except error.HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace")
                if not self._is_context_window_error(details):
                    raise RuntimeError(f"Local OpenAI-compatible HTTP {exc.code}: {details}") from exc
                retry_max_tokens = self._retry_max_tokens_for_context_error(
                    details=details,
                    current_max_tokens=int(current_payload["max_tokens"]),
                )
                if retry_max_tokens is not None:
                    current_payload["max_tokens"] = retry_max_tokens
                    continue
                trimmed_messages = self._trim_messages_for_context_retry(current_payload["messages"])
                if trimmed_messages is None:
                    raise RuntimeError(f"Local OpenAI-compatible HTTP {exc.code}: {details}") from exc
                current_payload["messages"] = trimmed_messages
                current_payload["max_tokens"] = min(self.settings.local_max_tokens, 128)
        raise RuntimeError(
            "Local OpenAI-compatible request kept exceeding the model context window "
            f"after repeated retries. Last attempted max_tokens={current_payload['max_tokens']}."
        )

    def _send_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.settings.llamacpp_chat_url,
            data=body,
            headers=self._build_headers(),
            method="POST",
        )
        with request.urlopen(req, timeout=self.settings.local_timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _retry_max_tokens_for_context_error(
        self,
        *,
        details: str,
        current_max_tokens: int,
    ) -> int | None:
        parsed_details = self._parse_error_json(details)
        message = str(parsed_details.get("error", {}).get("message") or details)
        if "maximum context length" not in message or "input tokens" not in message.lower():
            return None

        max_context_match = re.search(r"maximum context length is (\d+) tokens", message, flags=re.IGNORECASE)
        input_tokens_match = re.search(r"contains at least (\d+) input tokens", message, flags=re.IGNORECASE)
        if not max_context_match or not input_tokens_match:
            return None

        max_context = int(max_context_match.group(1))
        input_tokens = int(input_tokens_match.group(1))
        available = max_context - input_tokens - 1
        if available <= 0:
            return None

        safety_adjusted = available - 32 if available > 64 else available
        retry_max_tokens = min(current_max_tokens - 1, safety_adjusted)
        if retry_max_tokens <= 0 or retry_max_tokens >= current_max_tokens:
            return None
        return retry_max_tokens

    def _is_context_window_error(self, details: str) -> bool:
        parsed_details = self._parse_error_json(details)
        message = str(parsed_details.get("error", {}).get("message") or details)
        return "maximum context length" in message.lower() and "input tokens" in message.lower()

    def _trim_messages_for_context_retry(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        if len(messages) <= 6:
            return self._compact_messages_for_context_retry(messages)
        system_prefix: list[dict[str, Any]] = []
        remaining = list(messages)
        if remaining and remaining[0].get("role") == "system":
            system_prefix = [remaining.pop(0)]
        if not remaining:
            return None
        anchor = remaining[0]
        tail = remaining[-4:]
        trimmed: list[dict[str, Any]] = system_prefix + [anchor]
        for message in tail:
            if message is anchor:
                continue
            trimmed.append(message)
        if len(trimmed) >= len(messages):
            return self._compact_messages_for_context_retry(messages)
        return trimmed

    def _compact_messages_for_context_retry(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        if not messages:
            return None
        compacted: list[dict[str, Any]] = []
        changed = False
        for index, message in enumerate(messages):
            cloned = dict(message)
            content = cloned.get("content", "")
            if (
                isinstance(content, str)
                and len(content) > 350
                and not (index == 0 and cloned.get("role") == "system")
                and not (index == 1 and cloned.get("role") == "user")
            ):
                cloned["content"] = content[:220] + " ...[truncated]... " + content[-80:]
                changed = True
            compacted.append(cloned)
        return compacted if changed else None

    def _parse_error_json(self, details: str) -> dict[str, Any]:
        try:
            parsed = json.loads(details)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.llamacpp_api_key.strip():
            headers["Authorization"] = f"Bearer {self.settings.llamacpp_api_key}"
        return headers

    def _prepare_messages(
        self,
        messages: list[dict[str, Any]],
        *,
        require_json: bool,
    ) -> list[dict[str, Any]]:
        prepared = [
            {
                "role": message["role"],
                "content": message.get("content", ""),
            }
            for message in messages
        ]
        if require_json:
            format_instruction = (
                "FORMAT:\nReturn a single compact JSON object on one line only. "
                "Do not pretty-print, do not use markdown fences, and do not add extra commentary."
            )
            if prepared and prepared[0].get("role") == "system":
                prepared[0]["content"] = str(prepared[0].get("content", "")) + "\n\n" + format_instruction
            else:
                prepared.insert(0, {"role": "system", "content": format_instruction})
        return prepared

    def _coerce_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content)


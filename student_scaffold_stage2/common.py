from __future__ import annotations

from typing import Any

from course_project.json_tools import build_json_tools_prompt, serialize_feedback_payload
from course_project.student_api import StudentRuntime

from . import prompts


def build_system_prompt(
    runtime: StudentRuntime,
    *,
    memory_rules: list[str] | None = None,
) -> str:
    """Build the instruction string sent before the user's request."""
    return build_json_tools_prompt(
        rules=runtime.prompt_rules() + prompts.EXTRA_RULES + (memory_rules or []),
        tools=runtime.list_tools(),
        compact=runtime.compact_local_prompt,
    )


def assistant_message(response: Any) -> dict[str, Any]:
    """Convert a model response into a conversation message."""
    message: dict[str, Any] = {"role": "assistant", "content": response.content}
    if getattr(response, "reasoning_details", None) is not None:
        message["reasoning_details"] = response.reasoning_details
    message["_model_name"] = getattr(response, "model", "")
    return message


def tool_result_message(tool_name: str, result: Any) -> dict[str, str]:
    """Convert a tool result into the text you send back to the model."""
    return {
        "role": "user",
        "content": f"TOOL_RESULT {tool_name}: {serialize_feedback_payload(result)}",
    }


def extract_direct_time_preference(text: str) -> str | None:
    """Small starter rule for Stage 2.

    Stage 2 is allowed to use simple rules. Stage 3 replaces this with a
    learned extractor.
    """
    normalized = text.lower()
    if any(phrase in normalized for phrase in ("afternoon", "later", "late in the day")):
        return "afternoon"
    if any(phrase in normalized for phrase in ("morning", "earlier", "early in the day")):
        return "morning"
    return None


def latest_time_window(memories: list[dict[str, Any]]) -> str | None:
    for memory in reversed(memories):
        if memory.get("key") != "preferred_time_window":
            continue
        value = str(memory.get("value", "")).strip().lower()
        if value in {"morning", "afternoon"}:
            return value
    return None


def choose_preferred_slot(available_slots: list[str], preference: str | None) -> str | None:
    if not available_slots:
        return None
    if preference == "morning":
        return min(available_slots, key=_slot_minutes)
    if preference == "afternoon":
        return max(available_slots, key=_slot_minutes)
    return None


def _slot_minutes(slot: str) -> int:
    hour, minute = slot.split(":", 1)
    return int(hour) * 60 + int(minute)

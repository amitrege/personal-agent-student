from __future__ import annotations

from typing import Any

from course_project.json_tools import build_json_tools_prompt, serialize_feedback_payload
from course_project.student_api import StudentRuntime

from . import prompts


def build_system_prompt(runtime: StudentRuntime) -> str:
    """Build the instruction string sent before the user's request."""
    return build_json_tools_prompt(
        rules=runtime.prompt_rules() + prompts.EXTRA_RULES,
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


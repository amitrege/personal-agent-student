from __future__ import annotations

from course_project.student_api import StudentRuntime
from student_scaffold_stage2.common import (
    assistant_message,
    build_system_prompt as build_stage2_system_prompt,
    choose_preferred_slot,
    latest_time_window,
    tool_result_message,
)

from . import prompts
from .preference_extractor import build_extractor  # noqa: F401  (re-export for agent/mini use)


def build_system_prompt(
    runtime: StudentRuntime,
    *,
    memory_rules: list[str] | None = None,
) -> str:
    return build_stage2_system_prompt(
        runtime,
        memory_rules=prompts.EXTRA_RULES + (memory_rules or []),
    )


__all__ = [
    "assistant_message",
    "build_extractor",
    "build_system_prompt",
    "choose_preferred_slot",
    "latest_time_window",
    "tool_result_message",
]

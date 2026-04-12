from __future__ import annotations

from typing import Any

from course_project.json_tools import (
    exhausted_invalid_feedback,
    invalid_json_feedback,
    parse_action,
)
from course_project.student_api import SessionResult, StudentAgent, StudentRuntime

from .common import (
    assistant_message,
    build_system_prompt,
    choose_preferred_slot,
    extract_direct_time_preference,
    latest_time_window,
    tool_result_message,
)


class MemoryStudentAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime) -> SessionResult:  # noqa: ANN001
        """Stage-2 agent: your Stage-1 loop extended with persistent memory.

        Copy your Stage-1 run_session here, then add three pieces using the
        patterns from the mini-stages:

        BEFORE the tool loop:
          1. Detect a time preference in the user message; write it to memory
             if one is found.                                           (mini_1)
          2. Search memory for any stored preference for this user.
             Save the result — you'll use it at the create_event step.  (mini_2)

        INSIDE the tool loop:
          3. Each time find_free_slots returns, save the slot list. When the
             model then requests create_event, intercept the arguments and
             override start_time with the preferred slot if one exists.
             (mini_3 + mini_4)

        Edge cases to handle: what if create_event is requested before
        find_free_slots has run? What hint, if any, do you add to the system
        prompt when active_preference is set, and how do you word it?

        Do not hard-code users, note titles, dates, attendees, or expected slots.
        Hidden sessions use different values.
        """
        return runtime.finish(
            "Stage 2 agent is not implemented yet. Copy your Stage-1 loop into "
            "student_scaffold_stage2/agent.py, then add the memory pieces from the mini-stages."
        )


def build_agent(settings: Any) -> MemoryStudentAgent:
    return MemoryStudentAgent(settings)

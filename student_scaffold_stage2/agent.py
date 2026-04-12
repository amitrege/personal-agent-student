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

        Start by copying your Stage-1 run_session here. Then add three pieces —
        each one is a pattern you built in the mini-stages:

        BEFORE the tool loop:
          1. Detect whether the user message contains a time preference.
             If it does, write it to memory.                              (mini_1)
          2. Search memory for any stored preference for this user.
             Store the result — you will use it during slot selection.    (mini_2)

        INSIDE the tool loop, when the model requests calendar.create_event:
          3. If memory has an active preference and you have a list of
             free slots from find_free_slots, use choose_preferred_slot
             to pick the best one and override start_time.               (mini_3 + mini_4)

        Design choices you make here:
        - When `active_preference` is set, do you add a rule to the system
          prompt? If so, how do you word it so the model applies it correctly?
        - What happens if find_free_slots has not been called yet when
          create_event is requested? How do you handle that case safely?
        - The keyword rule extract_direct_time_preference only catches
          direct phrases. Is that acceptable for Stage 2? Why or why not?

        Do not hard-code users, note titles, dates, attendees, or expected slots.
        Hidden sessions use different values.
        """
        return runtime.finish(
            "Stage 2 agent is not implemented yet. Copy your Stage-1 loop into "
            "student_scaffold_stage2/agent.py, then add the memory pieces from the mini-stages."
        )


def build_agent(settings: Any) -> MemoryStudentAgent:
    return MemoryStudentAgent(settings)

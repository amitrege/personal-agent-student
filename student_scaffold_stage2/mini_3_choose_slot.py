from __future__ import annotations

from typing import Any

from course_project.student_api import StudentAgent, StudentRuntime

from .common import (
    choose_preferred_slot,
    extract_direct_time_preference,
    latest_time_window,
)


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 3: use memory to choose among valid free slots."""
        preference = extract_direct_time_preference(session.user_message)
        if preference is not None:
            runtime.write_memory(
                key="preferred_time_window",
                value=preference,
                evidence=session.user_message,
                confidence=1.0,
            )

        memories = runtime.search_memory(key="preferred_time_window")
        active_preference = latest_time_window(memories)
        available_slots = ["09:00", "16:00"]

        # -- YOUR TASK ---------------------------------------------------------
        # Replace `chosen_slot = ...` with choose_preferred_slot(...).
        # Pass the valid slots list and the active memory preference.
        chosen_slot = ...  # <- replace this

        # -- do not edit below this line --------------------------------------
        if chosen_slot is ...:
            raise NotImplementedError("Replace `chosen_slot = ...` with choose_preferred_slot(...).")
        return runtime.finish(
            f"preference={active_preference}; available_slots={available_slots}; chosen_slot={chosen_slot}"
        )


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

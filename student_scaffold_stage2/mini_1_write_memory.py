from __future__ import annotations

from typing import Any

from course_project.student_api import StudentAgent, StudentRuntime

from .common import extract_direct_time_preference


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 1: write one stated scheduling preference to memory."""
        preference = extract_direct_time_preference(session.user_message)
        if preference is None:
            return runtime.finish("No new time preference in this session.")

        # -- YOUR TASK ---------------------------------------------------------
        # Replace `memory = ...` with a runtime.write_memory() call.
        # See ARCHITECTURE.md under "The Memory API" for the call signature.
        # Think about what key, value, evidence, and confidence should be.
        memory = ...  # <- replace this

        # -- do not edit below this line --------------------------------------
        if memory is ...:
            raise NotImplementedError("Replace `memory = ...` with your runtime.write_memory() call.")
        return runtime.finish(f"Stored memory: {memory}")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

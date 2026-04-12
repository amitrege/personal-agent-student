from __future__ import annotations

from typing import Any

from course_project.student_api import StudentAgent, StudentRuntime

from .common import extract_direct_time_preference


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 2: retrieve a memory written in an earlier session."""
        preference = extract_direct_time_preference(session.user_message)
        if preference is not None:
            runtime.write_memory(
                key="preferred_time_window",
                value=preference,
                evidence=session.user_message,
                confidence=1.0,
            )

        # -- YOUR TASK ---------------------------------------------------------
        # Replace `memories = ...` with a runtime.search_memory() call.
        # Use the same key you wrote memory with in mini_1.
        memories = ...  # <- replace this

        # -- do not edit below this line --------------------------------------
        if memories is ...:
            raise NotImplementedError("Replace `memories = ...` with your runtime.search_memory() call.")
        return runtime.finish(f"{session.session_id} memories: {memories}")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

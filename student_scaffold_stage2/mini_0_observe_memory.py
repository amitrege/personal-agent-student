from __future__ import annotations

from typing import Any

from course_project.student_api import StudentAgent, StudentRuntime


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 0: observe the memory interface before writing code.

        This file has no TODO. Run it and read the output carefully.
        """

        print("\n=== User message ===")
        print(session.user_message)

        print("\n=== Memory mode ===")
        print(runtime.memory_mode)

        print("\n=== Existing preferred_time_window memories ===")
        memories = runtime.search_memory(key="preferred_time_window")
        print(memories)

        print("\n=== Memory API ===")
        print("runtime.write_memory(key=..., value=..., evidence=..., confidence=...)")
        print("runtime.search_memory(key='preferred_time_window')")

        return runtime.finish("Memory exploration complete.")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

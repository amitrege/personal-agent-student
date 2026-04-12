from __future__ import annotations

from typing import Any

from course_project.student_api import StudentAgent, StudentRuntime

from .common import build_system_prompt


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 1: call the model once and return what it said."""
        messages = [{"role": "user", "content": session.user_message}]
        system_prompt = build_system_prompt(runtime)

        # ── YOUR TASK ────────────────────────────────────────────────────────────
        # Replace `response = ...` with a call to runtime.complete().
        # The model needs both the system prompt and the user message.
        # Look up the call signature in ARCHITECTURE.md under "The Three Main Objects".
        response = ...  # ← replace this

        # ── do not edit below this line ──────────────────────────────────────
        if response is ...:
            raise NotImplementedError("Replace `response = ...` above with your runtime.complete() call.")
        return runtime.finish("Model said: " + response.content)


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)


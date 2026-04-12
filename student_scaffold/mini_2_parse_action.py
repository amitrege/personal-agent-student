from __future__ import annotations

from typing import Any

from course_project.json_tools import parse_action
from course_project.student_api import StudentAgent, StudentRuntime

from .common import assistant_message, build_system_prompt


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 2: call the model and parse its JSON action."""
        messages = [{"role": "user", "content": session.user_message}]
        system_prompt = build_system_prompt(runtime)
        response = runtime.complete(
            messages=[{"role": "system", "content": system_prompt}] + messages,
            require_json=True,
        )
        messages.append(assistant_message(response))

        # ── YOUR TASK ────────────────────────────────────────────────────────────
        # Replace `action = ...`. You have the model's response object.
        # parse_action() is already imported — figure out what to pass it.
        # The returned dict has 'tool_call' and 'final_response' keys.
        action = ...  # ← replace this

        # ── do not edit below this line ──────────────────────────────────────
        if action is ...:
            raise NotImplementedError("Replace `action = ...` above with your parse_action() call.")
        return runtime.finish("Parsed action: " + str(action))


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)


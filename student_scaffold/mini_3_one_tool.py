from __future__ import annotations

from typing import Any

from course_project.json_tools import parse_action
from course_project.student_api import StudentAgent, StudentRuntime

from .common import assistant_message, build_system_prompt


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 3: execute the first tool call the model requests."""
        messages = [{"role": "user", "content": session.user_message}]
        system_prompt = build_system_prompt(runtime)
        response = runtime.complete(
            messages=[{"role": "system", "content": system_prompt}] + messages,
            require_json=True,
        )
        messages.append(assistant_message(response))
        action = parse_action(response.content)
        tool_call = action.get("tool_call")
        if not tool_call:
            return runtime.finish(action.get("final_response", "The model did not ask for a tool."))

        # ── YOUR TASK ────────────────────────────────────────────────────────────
        # Replace the assignment below with a runtime.call_tool() call.
        # It returns three values: tool_name, arguments, result.
        # You have the tool name and arguments inside `tool_call` — pass them through.
        # See ARCHITECTURE.md under "The Three Main Objects" for the call signature.
        tool_name, arguments, result = None, None, None  # ← replace this line

        # ── do not edit below this line ──────────────────────────────────────
        if tool_name is None:
            raise NotImplementedError("Replace the assignment above with your runtime.call_tool() call.")
        return runtime.finish(f"Called {tool_name} with result: {result}")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)


from __future__ import annotations

from typing import Any

from course_project.json_tools import parse_action
from course_project.student_api import StudentAgent, StudentRuntime

from .common import assistant_message, build_system_prompt, tool_result_message


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 4: call one tool, send the result back, then ask the model again."""
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

        tool_name, arguments, result = runtime.call_tool(
            tool_name=tool_call.get("name"),
            arguments=tool_call.get("arguments", {}),
            turn_index=0,
        )

        # ── YOUR TASK ────────────────────────────────────────────────────────────
        # The tool result is in a Python variable. The model has not seen it yet.
        # Two things need to happen before the model can continue.
        # Think about what needs to change in `messages`, and what to call next.
        # Both helpers you need are already imported at the top of this file.
        second_response = ...  # ← replace this (after updating messages)

        # ── do not edit below this line ──────────────────────────────────────
        if second_response is ...:
            raise NotImplementedError(
                "Complete both steps in the TODO: append the tool result, then call runtime.complete()."
            )
        return runtime.finish("Second model response: " + second_response.content)


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)


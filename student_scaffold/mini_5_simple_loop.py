from __future__ import annotations

from typing import Any

from course_project.json_tools import parse_action
from course_project.student_api import StudentAgent, StudentRuntime

from .common import assistant_message, build_system_prompt, tool_result_message


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 5: combine the mini-stage pieces into a working loop.

        Everything below STEP 4 is already written for you — it is the same
        code you built across mini-stages 1 through 4, now inside a for loop.

        The only new concept is termination: the loop needs to know when to stop.
        That is your one task.

        When this works, run it with CLIENT=scripted and you will see your agent
        schedule the meeting end-to-end for the first time.
        """
        messages: list[dict[str, Any]] = [{"role": "user", "content": session.user_message}]
        final_response = ""

        for turn_index in range(runtime.max_model_turns):
            system_prompt = build_system_prompt(runtime)

            # STEP 1: call the model (same as mini_1)
            response = runtime.complete(
                messages=[{"role": "system", "content": system_prompt}] + messages,
                require_json=True,
            )

            # STEP 2: record the response and parse the action (same as mini_2)
            messages.append(assistant_message(response))
            action = parse_action(response.content)

            # STEP 3: if the model requested a tool, run it and send the result back (same as mini_3 + mini_4)
            tool_call = action.get("tool_call")
            if tool_call:
                tool_name, _, result = runtime.call_tool(
                    tool_name=tool_call.get("name"),
                    arguments=tool_call.get("arguments", {}),
                    turn_index=turn_index,
                )
                messages.append(tool_result_message(tool_name, result))
                # After appending the result, `continue` sends the loop back to STEP 1.
                # On the next iteration the model will see the tool result and ask for the next step.
                # This is how multi-turn works — the loop replaces the manual second call in mini_4.
                continue

            # STEP 4: if the model returned a final response, stop the loop.
            # The model signals it is done by setting final_response to a non-empty string.
            # Check action['final_response']. If it is non-empty, store it in `final_response` and break.
            # TODO: replace the `pass` below with your termination condition (~2 lines).
            pass  # ← your code goes here

        # Return the result. If the loop ended without a final response, use a fallback.
        return runtime.finish(final_response or runtime.default_final_response() or "Could not complete the task.")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

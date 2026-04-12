from __future__ import annotations

from typing import Any

from course_project.json_tools import (
    exhausted_invalid_feedback,
    invalid_json_feedback,
    parse_action,
)
from course_project.student_api import SessionResult, StudentAgent, StudentRuntime

from .common import assistant_message, build_system_prompt, tool_result_message


class BaselineStudentAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime) -> SessionResult:  # noqa: ANN001
        """Run one independent Stage-1 task.

        You built a working minimal loop in mini_5. This file is the same loop
        with two additions: error handling (what if the model returns bad JSON?)
        and design choices (what rules go in prompts.py?).

        Design choices are yours to make:
        - What rules go in prompts.py to guide the model toward the right tool sequence?
        - How do you handle turns where the model returns invalid JSON?
        - When is the agent truly done? (Hint: a final_response alone may not be enough.)

        Objects available:
        - session.user_message  : the user's request
        - runtime               : .complete(), .call_tool(), .finish(), .list_tools()
        - messages              : the conversation history you build up each turn
        """
        messages: list[dict[str, Any]] = [{"role": "user", "content": session.user_message}]
        invalid_response_count = 0
        final_response = ""

        for turn_index in range(runtime.max_model_turns):
            system_prompt = build_system_prompt(runtime)

            # STEP 1: Call the model — same pattern as mini-stage 1.
            # runtime.complete(messages=..., require_json=True)
            # Prepend {"role": "system", "content": system_prompt} to messages.
            # TODO ↓

            # STEP 2: Record the response and parse the action.
            # Same as mini-stage 2, with ONE NEW ADDITION: wrap parse_action in try/except.
            #   - Append assistant_message(response) to messages first.
            #   - try: action = parse_action(response.content)
            #   - except: increment invalid_response_count,
            #             append {"role": "user", "content": invalid_json_feedback()} to messages,
            #             then `continue`.
            # (invalid_json_feedback is already imported at the top of this file)
            # TODO ↓

            # STEP 3: If the model requested a tool, run it and loop back.
            # Same pattern as mini-stages 3 + 4.
            # check action.get("tool_call"), call runtime.call_tool(..., turn_index=turn_index),
            # append tool_result_message(tool_name, result), then `continue`.
            # TODO ↓

            # STEP 4: If the model is done, store the answer and stop.
            # Same pattern as mini-stage 5.
            # check action.get("final_response"), store in final_response, break.
            # TODO ↓

        # Return the result to the benchmark.
        # runtime.finish() packages final_response into a SessionResult.
        # The two fallbacks below handle edge cases:
        #   - exhausted_invalid_feedback(): the model never returned valid JSON
        #   - starter fallback: the loop ended without any response because
        #     the TODOs above have not been implemented yet
        if not final_response and invalid_response_count > 0:
            final_response = exhausted_invalid_feedback()
        if not final_response:
            final_response = (
                "Stage 1 agent is not implemented yet. Complete the TODOs in "
                "student_scaffold/agent.py, then rerun the benchmark."
            )
        return runtime.finish(final_response)


def build_agent(settings: Any) -> BaselineStudentAgent:
    return BaselineStudentAgent(settings)

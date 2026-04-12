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
        """Run one Stage-1 scheduling session.

        This is the same four-step loop from mini-stages 1–5, assembled into
        a working agent. The loop calls the model, parses the response, runs
        the requested tool, and repeats until the model returns a final answer.

        Design choices are yours:
        - What rules go in prompts.py? (Run mini-stage 6 to see the baseline first.)
        - How many invalid-JSON retries before giving up?
        - When is the agent truly done — final_response alone, or verified event creation?
        """
        messages: list[dict[str, Any]] = [{"role": "user", "content": session.user_message}]
        invalid_response_count = 0
        final_response = ""

        for turn_index in range(runtime.max_model_turns):
            system_prompt = build_system_prompt(runtime)

            # STEP 1 — Ask the model what to do next.  (mini-stage 1)
            # TODO ↓

            # STEP 2 — Record the response and parse the action.  (mini-stage 2)
            # Append assistant_message(response) to messages, then parse.
            # Wrap parse_action in try/except to handle malformed JSON.
            # TODO ↓

            # STEP 3 — If the model requested a tool, run it and loop back.  (mini-stages 3+4)
            # TODO ↓

            # STEP 4 — If the model is done, store the answer and stop.  (mini-stage 5)
            # TODO ↓

        # Return the result to the benchmark.
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

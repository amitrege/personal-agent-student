from __future__ import annotations

from typing import Any

from course_project.student_api import StudentAgent, StudentRuntime

from .common import build_system_prompt


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 0: observe everything the agent knows before writing any code.

        This file has no TODO. Run it and read the output carefully.
        Everything printed here is available to your agent code.
        """

        # ── 1. The user's request ────────────────────────────────────────────
        print("\n=== User message ===")
        print(session.user_message)

        # ── 2. The available tools ───────────────────────────────────────────
        # These are the tools your agent can call. Read the names — you will
        # use them in prompts.py and see them in the model's JSON responses.
        print("\n=== Available tools ===")
        for tool in runtime.list_tools():
            print(f"  {tool.name}")
            print(f"    {tool.description}")
            if tool.parameters:
                print(f"    parameters: {list(tool.parameters.keys())}")

        # ── 3. The full system prompt ────────────────────────────────────────
        # This is the instruction block the model receives before your message.
        # It describes every tool in detail, the expected JSON response format,
        # and your custom rules from prompts.py. Read it — this is what the
        # model sees when it decides which tool to call.
        print("\n=== System prompt (what the model receives as instructions) ===")
        print(build_system_prompt(runtime))

        # ── Return a valid result ────────────────────────────────────────────
        return runtime.finish("Exploration complete.")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

from __future__ import annotations

from typing import Any

from course_project.json_tools import build_json_tools_prompt, parse_action
from course_project.student_api import StudentAgent, StudentRuntime

from .common import assistant_message, tool_result_message


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 6: observe what the model does with minimal prompt guidance.

        This file is already complete — do not edit it.
        Run it with CLIENT=local and watch what happens turn by turn.
        Your job is to observe, not to implement.

        The agent loop here is identical to mini_5, but the system prompt is built
        with ONLY the default benchmark rules — no EXTRA_RULES from prompts.py.
        This shows you the model's baseline behavior before any custom guidance.
        """
        # Build system prompt using only the benchmark's default rules.
        # Note: build_system_prompt from common.py would add prompts.EXTRA_RULES.
        # Here we deliberately omit them to expose baseline behavior.
        system_prompt = build_json_tools_prompt(
            rules=runtime.prompt_rules(),  # default rules only
            tools=runtime.list_tools(),
            compact=runtime.compact_local_prompt,
        )

        messages: list[dict[str, Any]] = [{"role": "user", "content": session.user_message}]
        final_response = ""

        print(f"\n{'=' * 60}")
        print(f"SESSION : {session.session_id}")
        print(f"REQUEST : {session.user_message}")
        print(f"PROMPTS : default benchmark rules only (no EXTRA_RULES)")
        print(f"{'=' * 60}")

        for turn_index in range(runtime.max_model_turns):
            response = runtime.complete(
                messages=[{"role": "system", "content": system_prompt}] + messages,
                require_json=True,
            )
            messages.append(assistant_message(response))

            try:
                action = parse_action(response.content)
            except Exception as exc:
                print(f"\n[Turn {turn_index}] INVALID JSON — model did not follow format: {exc}")
                print(f"  Raw: {response.content[:300]}")
                break

            tool_call = action.get("tool_call")
            if tool_call:
                tool_name = tool_call.get("name", "?")
                arguments = tool_call.get("arguments", {})
                print(f"\n[Turn {turn_index}] TOOL CALL : {tool_name}")
                print(f"             args     : {arguments}")
                try:
                    tool_name, _, result = runtime.call_tool(
                        tool_name=tool_name,
                        arguments=arguments,
                        turn_index=turn_index,
                    )
                    result_preview = str(result)[:400]
                    print(f"             result   : {result_preview}")
                    messages.append(tool_result_message(tool_name, result))
                except Exception as exc:
                    print(f"             ERROR    : {exc}")
                    break
                continue

            final_response = action.get("final_response", "")
            if final_response:
                print(f"\n[Turn {turn_index}] FINAL RESPONSE : {final_response}")
            else:
                print(f"\n[Turn {turn_index}] No tool call and no final response — loop ended.")
            break

        print(f"\n{'─' * 60}")
        print("OBSERVE — think about what you saw:")
        print("  Did the model open the note or thread before scheduling?")
        print("  Did it call calendar.find_free_slots?")
        print("  Did it pick a slot that avoids existing calendar conflicts?")
        print("  What rules would change this behavior?")
        print(f"{'─' * 60}\n")

        return runtime.finish(final_response or runtime.default_final_response() or "No final response.")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

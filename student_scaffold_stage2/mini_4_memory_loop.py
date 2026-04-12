from __future__ import annotations

from typing import Any

from course_project.json_tools import parse_action
from course_project.student_api import StudentAgent, StudentRuntime

from .common import (
    assistant_message,
    build_system_prompt,
    choose_preferred_slot,
    extract_direct_time_preference,
    latest_time_window,
    tool_result_message,
)


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 4: add memory-based slot choice to the Stage-1 loop."""
        preference = extract_direct_time_preference(session.user_message)
        if preference is not None:
            runtime.write_memory(
                key="preferred_time_window",
                value=preference,
                evidence=session.user_message,
                confidence=1.0,
            )

        memories = runtime.search_memory(key="preferred_time_window")
        active_preference = latest_time_window(memories)
        memory_rules = []
        if active_preference:
            memory_rules.append(
                "Memory says preferred_time_window="
                f"{active_preference}. Use it only to choose among valid free slots."
            )

        messages: list[dict[str, Any]] = [{"role": "user", "content": session.user_message}]
        final_response = ""
        last_available_slots: list[str] = []

        for turn_index in range(runtime.max_model_turns):
            system_prompt = build_system_prompt(runtime, memory_rules=memory_rules)
            response = runtime.complete(
                messages=[{"role": "system", "content": system_prompt}] + messages,
                require_json=True,
            )
            messages.append(assistant_message(response))
            action = parse_action(response.content)

            tool_call = action.get("tool_call")
            if tool_call:
                raw_tool_name = tool_call.get("name")
                arguments = dict(tool_call.get("arguments", {}))

                if str(raw_tool_name).endswith("create_event"):
                    # -- YOUR TASK ---------------------------------------------
                    # Replace `preferred_slot = ...` with choose_preferred_slot(...).
                    # If preferred_slot is not None, set arguments["start_time"] to it.
                    preferred_slot = ...  # <- replace this
                    if preferred_slot is ...:
                        raise NotImplementedError(
                            "Replace `preferred_slot = ...` with choose_preferred_slot(...)."
                        )
                    if preferred_slot:
                        arguments["start_time"] = preferred_slot

                tool_name, _, result = runtime.call_tool(
                    tool_name=raw_tool_name,
                    arguments=arguments,
                    turn_index=turn_index,
                )
                if tool_name == "calendar.find_free_slots" and isinstance(result, dict):
                    slots = result.get("available_slots", [])
                    last_available_slots = [str(slot) for slot in slots if isinstance(slot, str)]
                messages.append(tool_result_message(tool_name, result))
                continue

            final_response = action.get("final_response", "").strip()
            if final_response:
                break

        return runtime.finish(final_response or runtime.default_final_response() or "Could not complete the task.")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

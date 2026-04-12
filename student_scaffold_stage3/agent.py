from __future__ import annotations

from typing import Any

from course_project.json_tools import (
    exhausted_invalid_feedback,
    invalid_json_feedback,
    missing_finish_feedback,
    parse_action,
)
from course_project.student_api import SessionResult, StudentAgent, StudentRuntime

from .common import (
    assistant_message,
    build_extractor,
    build_system_prompt,
    choose_preferred_slot,
    latest_time_window,
    tool_result_message,
)


class LearnedMemoryStudentAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings
        # build_extractor is defined in preference_extractor.py — implement it there.
        self.extractor = build_extractor(settings)

    def run_session(self, session, runtime: StudentRuntime) -> SessionResult:  # noqa: ANN001
        """Final Stage-3 agent: learned memory writer plus Stage-2 memory loop.

        What is provided here
        ---------------------
        The full Stage-2 memory loop (search memory → build system prompt →
        tool loop → choose preferred slot → create event) is already written
        below. You should not need to change it.

        What you write
        --------------
        The two STAGE-3 STEP blocks at the top of this function call your
        classifier (from preference_extractor.py) and write to memory.
        These are the only TODOs.

        Design choice: confidence threshold
        -----------------------------------
        The write block should include a condition on prediction.confidence.
        See ARCHITECTURE.md "The Confidence Field" and the evaluation you
        ran in mini-stage 1 to choose a threshold. Add it as a constant or
        a settings field — not a magic number buried in the condition.
        """

        # -- STAGE-3 STEP 1 ----------------------------------------------------
        # Call your classifier on the user message.
        # Use self.extractor.predict(...) — it returns a Prediction with
        # .label and .confidence.
        prediction = self.extractor.predict(session.user_message)  # implement the extractor in preference_extractor.py

        # -- STAGE-3 STEP 2 ----------------------------------------------------
        # Conditionally write memory.
        # Write when the label is "morning" or "afternoon" AND confidence
        # is above your threshold. Do not write for "none".
        # Pass prediction.confidence (not 1.0) as the confidence argument.
        #
        # TODO: Replace 1.0 with a threshold calibrated from your mini-stage 1
        # output. 1.0 is a placeholder — no real classifier reaches it, so
        # this block won't fire until you change it. Use your mini-stage 1
        # confidence distributions to pick a value you can justify.
        if prediction.label in {"morning", "afternoon"} and prediction.confidence >= 1.0:  # TODO: replace 1.0
            runtime.write_memory(
                key="preferred_time_window",
                value=prediction.label,
                evidence=session.user_message,
                confidence=prediction.confidence,
            )

        # -- Stage-2 memory loop (provided) ------------------------------------
        memories = runtime.search_memory(key="preferred_time_window")
        active_preference = latest_time_window(memories)
        memory_rules = []
        if active_preference:
            memory_rules.append(
                "Learned memory says preferred_time_window="
                f"{active_preference}. Use it only to choose among valid free slots."
            )

        messages: list[dict[str, Any]] = [{"role": "user", "content": session.user_message}]
        invalid_response_count = 0
        final_response = ""
        last_available_slots: list[str] = []

        for turn_index in range(runtime.max_model_turns):
            system_prompt = build_system_prompt(runtime, memory_rules=memory_rules)
            response = runtime.complete(
                messages=[{"role": "system", "content": system_prompt}] + messages,
                require_json=True,
            )
            messages.append(assistant_message(response))

            try:
                action = parse_action(response.content)
            except Exception:
                invalid_response_count += 1
                messages.append({"role": "user", "content": invalid_json_feedback()})
                continue

            tool_call = action.get("tool_call")
            if tool_call:
                raw_tool_name = tool_call.get("name")
                arguments = dict(tool_call.get("arguments", {}))
                if str(raw_tool_name).endswith("create_event"):
                    preferred_slot = choose_preferred_slot(last_available_slots, active_preference)
                    if preferred_slot:
                        arguments["start_time"] = preferred_slot

                try:
                    tool_name, _, result = runtime.call_tool(
                        tool_name=raw_tool_name,
                        arguments=arguments,
                        turn_index=turn_index,
                    )
                except KeyError:
                    messages.append(
                        {
                            "role": "user",
                            "content": f"That tool is unavailable: {raw_tool_name}. Reply with valid JSON only.",
                        }
                    )
                    continue

                if tool_name == "calendar.find_free_slots" and isinstance(result, dict):
                    slots = result.get("available_slots", [])
                    last_available_slots = [str(slot) for slot in slots if isinstance(slot, str)]
                messages.append(tool_result_message(tool_name, result))
                continue

            final_response = action.get("final_response", "").strip()
            if final_response:
                break
            messages.append({"role": "user", "content": missing_finish_feedback()})

        if not final_response:
            final_response = runtime.default_final_response()
            if not final_response and invalid_response_count > 0:
                final_response = exhausted_invalid_feedback()
            if not final_response:
                final_response = "Could not complete the task."

        return runtime.finish(final_response)


def build_agent(settings: Any) -> LearnedMemoryStudentAgent:
    return LearnedMemoryStudentAgent(settings)

from __future__ import annotations

from typing import Any

from course_project.json_tools import (
    exhausted_invalid_feedback,
    invalid_json_feedback,
    missing_finish_feedback,
    parse_action,
)
from course_project.student_api import SessionResult, StudentAgent, StudentRuntime

# Import from Stage 3 so you do not have to duplicate the full agent.
# Your Stage-3 preference_extractor.py must be working before this will run.
from student_scaffold_stage3.common import (
    assistant_message,
    build_system_prompt,
    choose_preferred_slot,
    latest_time_window,
    tool_result_message,
)
from student_scaffold_stage3.preference_extractor import build_extractor


class SocialArenaAgent(StudentAgent):
    """Optional social-arena agent: your Stage-3 agent with stronger social behavior.

    Your Stage-3 agent can already enter the arena with:

        bash launch social

    This file is for extra credit. Start by copying your Stage-3 run_session
    here as the base. Then improve it so it beats the Stage-3 baseline on
    messier multi-session users.

    TACTIC A — Read preferences from artifacts.
        Stage 3 classifies only session.user_message. In the social arena, a
        note or email body may contain a preference after the agent opens it.
        After simple_note.show_note or gmail.show_thread, classify the artifact
        text too. If it contains a stable preference, write it to memory and
        use it for the current slot choice.

    TACTIC B — Handle temporary overrides and hard negatives.
        Treat "for this meeting only, later is better" as a current-session
        preference, not a permanent memory. Treat "mornings are impossible
        today" as "avoid morning for this session", not as a morning
        preference.

    TACTIC C — Use memory history more carefully.
        The memory list keeps every write for a key. Stage 3 usually trusts the
        latest write. Try a different policy: require repeated evidence, use
        confidence scores, ignore low-confidence writes, or handle temporary
        entries differently.

    You may also implement your own strategy. The leaderboard rewards behavior,
    not choosing one of the named tactics.

    See CHALLENGE.md for the full instructions and checkpoint.
    """

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        # Same classifier as Stage 3 — useful for artifact text, overrides,
        # and other custom social strategies.
        self.extractor = build_extractor(settings)

    def run_session(self, session, runtime: StudentRuntime) -> SessionResult:  # noqa: ANN001
        # Step 1: Copy your Stage-3 run_session implementation here.
        # Step 2: Add one or more social improvements on top.
        #
        # Tactic A: after opening a note or email thread, inspect the tool
        #   result text for preferences and update active_preference.
        #
        # Tactic B: detect temporary phrases and hard negatives before the
        #   memory write, then use them only for the current session.
        #
        # Tactic C: modify how you read and interpret the memory list after
        #   runtime.search_memory.
        #
        # Or design a different policy if you think it will serve users better.
        return runtime.finish(
            "Social arena agent is not implemented yet. Copy your Stage-3 run_session "
            "here and add social-arena logic for extra credit."
        )


def build_agent(settings: Any) -> SocialArenaAgent:
    return SocialArenaAgent(settings)

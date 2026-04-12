from __future__ import annotations

from typing import Any

from course_project.student_api import StudentAgent, StudentRuntime
from student_scaffold_stage2.common import extract_direct_time_preference


# Pairs of (expected_label, text) — expected_label is what a correct classifier should return.
_TEST_CASES = [
    # Direct phrases — the Stage-2 rule catches these
    ("morning",   "I prefer morning meetings when there is a choice."),
    ("afternoon", "Afternoon slots work better for me."),
    # Paraphrases — the Stage-2 rule misses these
    ("morning",   "I like to wrap things up before lunch."),
    ("morning",   "I am sharper in the first half of the day."),
    ("morning",   "The first half of the day suits me better for calls."),
    ("afternoon", "The second half of the day works better for me."),
    ("afternoon", "My schedule is usually clear from 2pm onward."),
    ("afternoon", "After lunch tends to be less hectic for me."),
    # No preference expressed
    ("none",      "Use my SimpleNote note to schedule the meeting."),
    ("none",      "Find the details in the email thread and create the event."),
    # Hard negatives — the text mentions a time of day but expresses the OPPOSITE
    ("none",      "Mornings are impossible for me this week."),
    ("none",      "My afternoons are usually packed with back-to-back meetings."),
]


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 0: observe where the Stage-2 rule fails."""

        print("\n=== Stage-2 rule results on test cases ===")
        print(f"{'EXPECTED':12s}  {'DETECTED':12s}  CASE")
        print("-" * 72)
        correct = 0
        for expected_label, text in _TEST_CASES:
            detected = extract_direct_time_preference(text)
            detected_str = detected if detected is not None else "none"
            marker = "OK  " if detected_str == expected_label else "MISS"
            if detected_str == expected_label:
                correct += 1
            print(f"{expected_label:12s}  {detected_str:12s}  [{marker}] {text}")

        total = len(_TEST_CASES)
        print(f"\nRule accuracy: {correct}/{total}")
        print(
            "\nWhat to observe:"
            "\n  - Which categories does the rule miss?"
            "\n  - Why does the rule fail on 'before lunch' or 'second half of the day'?"
            "\n  - Does the rule correctly reject the hard negatives at the bottom?"
            "\n  - A trained classifier must do better on the paraphrases without breaking the hard negatives."
        )
        return runtime.finish("Stage-2 gap exploration complete.")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

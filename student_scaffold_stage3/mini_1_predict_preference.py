from __future__ import annotations

from typing import Any

from course_project.student_api import StudentAgent, StudentRuntime

from .preference_extractor import build_extractor


# A held-out set for diagnosing your classifier's failure modes.
#
# Do not copy these exact diagnostic sentences into your training data.
# That is memorizing a visible diagnostic, not building a classifier.
# The graded benchmark uses different users and different phrasings, so
# copying these cases can raise this mini-stage score while doing little
# for your actual grade.
#
# Use this eval to diagnose failure modes (which class? which phrasing type?)
# and fix the underlying problem with broader, more diverse training data.
_EVAL_CASES: list[tuple[str, str]] = [
    # label, text
    ("morning",   "I prefer morning meetings when there is a choice."),
    ("morning",   "I like to wrap things up before lunch."),
    ("morning",   "I am sharper in the first half of the day."),
    ("morning",   "Early slots work better for my concentration."),
    ("morning",   "If possible, please schedule me before noon."),
    ("morning",   "I do my best thinking near the start of the day."),
    ("morning",   "My focus is usually clearest while the day is still fresh."),
    ("afternoon", "Afternoon slots work better for me."),
    ("afternoon", "The second half of the day works better for me."),
    ("afternoon", "My schedule is usually clear from 2pm onward."),
    ("afternoon", "After lunch tends to be less hectic for me."),
    ("afternoon", "Later in the day is better when I have options."),
    ("afternoon", "I usually hit my stride once the afternoon gets moving."),
    ("afternoon", "I warm up slowly, so later slots are usually better."),
    ("none",      "Use my SimpleNote note to schedule the meeting."),
    ("none",      "Find the details in the email thread and create the event."),
    ("none",      "Please put this on my calendar."),
    # Hard negatives — these contain time-of-day words but are NOT preferences
    ("none",      "Mornings are impossible for me this week."),
    ("none",      "My afternoons are usually packed with back-to-back meetings."),
    ("none",      "I try to keep my evenings free, so any work time is fine."),
    ("none",      "My morning is blocked today, but any open slot from the note is fine."),
    ("none",      "The email mentions an afternoon deadline, not a meeting preference."),
]


def _print_confusion_matrix(results: list[tuple[str, str]]) -> None:
    classes = ["morning", "afternoon", "none"]
    matrix: dict[str, dict[str, int]] = {a: {p: 0 for p in classes} for a in classes}
    for actual, pred in results:
        if actual in matrix and pred in matrix:
            matrix[actual][pred] += 1

    col_w = 10
    print(f"\n{'':14s}", end="")
    for c in classes:
        print(f"  {c[:col_w]:>{col_w}s}", end="")
    print("  <- predicted")
    for actual in classes:
        print(f"{actual:14s}", end="")
        for pred in classes:
            print(f"  {matrix[actual][pred]:>{col_w}d}", end="")
        print()
    print("^ actual")


class MiniStageAgent(StudentAgent):
    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.extractor = build_extractor(settings)

    def run_session(self, session, runtime: StudentRuntime):  # noqa: ANN001
        """Mini-stage 1: evaluate your classifier on a held-out test set."""

        print(f"\n=== Classifier evaluation ({len(_EVAL_CASES)} held-out cases) ===")
        results: list[tuple[str, str]] = []
        errors: list[tuple[str, str, float, str]] = []

        for actual_label, text in _EVAL_CASES:
            prediction = self.extractor.predict(text)
            results.append((actual_label, prediction.label))
            if prediction.label != actual_label:
                errors.append((actual_label, prediction.label, prediction.confidence, text))

        correct = sum(1 for a, p in results if a == p)
        print(f"\nOverall accuracy: {correct}/{len(results)}")

        _print_confusion_matrix(results)

        if errors:
            print(f"\nMispredictions ({len(errors)}):")
            for actual, pred, conf, text in errors:
                print(f"  expected={actual:9s}  got={pred:9s}  conf={conf:.2f}  {text!r}")
        else:
            print("\nAll held-out cases correct!")

        print(
            "\nWhat to think about:"
            "\n  - Are errors concentrated in one class? Add more training examples for that class."
            "\n  - Do the hard negatives ('Mornings are impossible') confuse your classifier?"
            "\n    If so, add negative-framing examples to your training data."
            "\n  - Look at the confidence values for correct predictions vs. errors."
            "\n    What threshold would reduce wrong writes without filtering too many correct ones?"
            "\n  - If accuracy is low overall, consider whether your features capture semantics"
            "\n    beyond keyword presence."
        )
        return runtime.finish("Classifier evaluation complete.")


def build_agent(settings: Any) -> MiniStageAgent:
    return MiniStageAgent(settings)

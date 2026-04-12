from __future__ import annotations

# Stage 3: implement your preference extractor here.
#
# Requirements
# ------------
# Your extractor must expose two things:
#
#   class PreferenceExtractor:
#       def predict(self, text: str) -> Prediction: ...
#
#   def build_extractor(settings) -> PreferenceExtractor: ...
#
# `build_extractor` is called once when the agent starts up. It should load
# or construct a trained classifier and return it. `predict` is called once
# per session with the user message and must return a Prediction.
#
# The Prediction dataclass is defined below — do not change its field names,
# since the agent and mini-stages depend on `.label` and `.confidence`.
#
# What the classifier must do
# ---------------------------
# Given any user message, predict one of three labels:
#
#   "morning"    the message suggests a morning scheduling preference
#   "afternoon"  the message suggests an afternoon scheduling preference
#   "none"       the message does not express a scheduling preference
#
# `confidence` is a float 0.0–1.0 expressing how certain the classifier is
# about the label. You decide what the threshold should be in agent.py.
#
# Design choices (see ARCHITECTURE.md for a fuller discussion)
# ------------------------------------------------------------
# - What algorithm will you use? (Naive Bayes, logistic regression, other?)
# - What features will you extract? (word counts, n-grams, embeddings?)
# - Where will you store training data and the trained model?
# - How will you handle the load/train decision in build_extractor?
#
# Hard cases to think about
# -------------------------
# "Mornings are impossible for me."  — contains "morning" but NOT a morning preference
# "My afternoons are packed."        — contains "afternoon" but NOT an afternoon preference
# "I work best before lunch."        — morning preference with no keyword match
# "The second half of the day suits me." — afternoon preference, unusual phrasing
#
# A classifier that merely checks for keyword presence will fail on these.
# Your training data should include examples like these.

from dataclasses import dataclass
from typing import Any


@dataclass
class Prediction:
    label: str         # "morning", "afternoon", or "none"
    confidence: float  # 0.0 to 1.0


class PreferenceExtractor:
    """Starter preference classifier.

    Suggestions:
    - Train in a separate script; load the saved model here.
    - Store the model file under stage3_artifacts/ and commit it (it is tracked by git).
    - Keep predict() fast — it is called once per session.

    The starter version predicts "none" for every message so the benchmark can
    run before you implement the learned component. Replace this with a real
    classifier for Stage 3.
    """

    def predict(self, text: str) -> Prediction:
        return Prediction(label="none", confidence=0.0)


def build_extractor(settings: Any) -> PreferenceExtractor:
    """Load or construct your trained extractor.

    Called once at agent startup. `settings.root` is the project root
    directory if you need it to locate training data or a saved model.

    Return a PreferenceExtractor instance ready to call .predict() on user
    messages. The starter implementation below is intentionally weak; replace
    it with code that loads your trained model.
    """
    return PreferenceExtractor()

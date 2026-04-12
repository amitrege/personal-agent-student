from __future__ import annotations

# Stage 3: implement your preference extractor here.
#
# This file replaces the Stage-2 keyword rule with a trained classifier.
# Instead of checking for exact phrases, your classifier learns from labeled
# examples and generalizes to phrasings it hasn't seen.
#
# Interface:
#   class PreferenceExtractor:
#       def predict(self, text: str) -> Prediction: ...
#
#   def build_extractor(settings) -> PreferenceExtractor: ...
#
# `build_extractor` is called once at agent startup — load your trained model
# and return a ready extractor. `predict` is called once per session.
# Don't change the Prediction field names; the agent and mini-stages depend
# on `.label` and `.confidence`.
#
# Classification task: given a user message, predict one of:
#   "morning"    the message suggests a morning scheduling preference
#   "afternoon"  the message suggests an afternoon scheduling preference
#   "none"       no scheduling preference expressed
#
# `confidence` (0.0–1.0) reflects how certain the classifier is. You set the
# write-to-memory threshold in agent.py based on what you observe in mini-stage 1.
#
# Hard cases — train on all four patterns:
#   "Mornings are impossible for me."      → none      (time word, but a constraint not a preference)
#   "My afternoons are packed."            → none      (same trap)
#   "I work best before lunch."            → morning   (preference, no obvious keyword)
#   "The second half of the day suits me." → afternoon (unusual phrasing)
#
# Design decisions (see ARCHITECTURE.md for the full discussion):
# - Algorithm: Naive Bayes, TF-IDF + logistic regression, embeddings, LLM-based?
# - Features: word counts, n-grams, sentence embeddings?
# - Where to save the trained model: stage3_artifacts/ (tracked by git)
# - How build_extractor locates the model: use settings.root for the repo root path

from dataclasses import dataclass
from typing import Any


@dataclass
class Prediction:
    label: str         # "morning", "afternoon", or "none"
    confidence: float  # 0.0 to 1.0


class PreferenceExtractor:
    """Preference classifier.

    Suggestions:
    - Train in a separate script; load the saved model here.
    - Store the model file under stage3_artifacts/ and commit it (it is tracked by git).
    - Keep predict() fast — it is called once per session.

    Replace this with your classifier.
    """

    def predict(self, text: str) -> Prediction:
        return Prediction(label="none", confidence=0.0)


def build_extractor(settings: Any) -> PreferenceExtractor:
    """Load your trained extractor.

    Called once at agent startup. `settings.root` is the project root
    directory — use it to locate your saved model. Replace the stub below
    with code that loads the model your training script saved.

    Expected load pattern (adjust to match your training script):

        import pickle, pathlib
        model_path = pathlib.Path(settings.root) / "stage3_artifacts" / "model.pkl"
        with model_path.open("rb") as f:
            model = pickle.load(f)
        return PreferenceExtractor(model)

    If this raises FileNotFoundError, run your training script first:
        python -m student_scaffold_stage3.train
    """
    return PreferenceExtractor()

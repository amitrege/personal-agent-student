"""Training script for the Stage-3 preference classifier.

Run from the repo root:
    python -m student_scaffold_stage3.train
or:
    python student_scaffold_stage3/train.py

This script loads labeled examples, trains your classifier, and saves the
result to stage3_artifacts/model.pkl. build_extractor() in
preference_extractor.py loads the model from that path at agent startup.

Commit the saved model file as part of your submission — the grader
imports your code and needs the model file present.
"""
from __future__ import annotations

import json
import pathlib
import pickle

# ---------------------------------------------------------------------------
# Paths — these match what build_extractor() expects. Do not change them.
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).parent.parent
DATA_FILE = ROOT / "training_data" / "preference_examples.jsonl"
ARTIFACTS_DIR = ROOT / "stage3_artifacts"
MODEL_FILE = ARTIFACTS_DIR / "model.pkl"


def main() -> None:
    # -----------------------------------------------------------------------
    # Load labeled examples
    # -----------------------------------------------------------------------
    examples = []
    with DATA_FILE.open() as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))

    texts = [ex["text"] for ex in examples]
    labels = [ex["label"] for ex in examples]

    label_counts = {label: labels.count(label) for label in set(labels)}
    print(f"Loaded {len(examples)} examples  —  class counts: {label_counts}")

    # -----------------------------------------------------------------------
    # TODO: Train your classifier.
    #
    # Choose your algorithm and features, fit the model, and assign it to
    # `model`. The model must be serializable with pickle. See
    # ARCHITECTURE.md "Algorithm choices" for the tradeoffs between the
    # options. Split out a validation set before fitting and evaluate
    # per-class accuracy — do not train and evaluate on the same data.
    # -----------------------------------------------------------------------
    model = None  # replace with your fitted model

    # -----------------------------------------------------------------------
    # Save the model — build_extractor() will load it from MODEL_FILE.
    # -----------------------------------------------------------------------
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    with MODEL_FILE.open("wb") as f:
        pickle.dump(model, f)

    print(f"Saved model → {MODEL_FILE}")


if __name__ == "__main__":
    main()

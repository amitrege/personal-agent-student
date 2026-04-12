# Stage-3 Mini-Stages

Stage 3 has a different workflow from Stages 1 and 2. In those stages you could run each mini-stage immediately. Here, mini-stage 1 requires a trained classifier — you have to build it first.

**Run mini-stage 0 first (no classifier needed):**

```bash
CLIENT=scripted bash launch stage3-mini0
```

It shows exactly where the Stage-2 keyword rule fails. Then read these three sections of `ARCHITECTURE.md` before writing any classifier code (about 8 minutes):

- **"Your Task: Build a Preference Classifier"** — defines the three-class problem (`morning` / `afternoon` / `none`), the interface your classifier must satisfy, and the algorithm options.
- **"Why Not Just Ask the LLM?"** — tradeoffs between a local trained classifier and using the LLM directly. Read this before choosing your approach.
- **"Training Data Strategy"** — the difference between fitting to the visible diagnostic set and building something that generalizes. This is the most common source of grading surprises in Stage 3.

**Work through the stages in this order:**
1. Run mini-stage 0 (above)
2. Read the three `ARCHITECTURE.md` sections above
3. Implement your classifier in `preference_extractor.py` and implement the training script in `train.py`
4. Train your classifier and save the model to `stage3_artifacts/`
5. Run mini-stage 1 (evaluates your classifier on a held-out diagnostic set)
6. Run mini-stage 2 (connects your classifier to the agent loop)
7. Implement `agent.py`

**Where to put things:**
- Your classifier: `student_scaffold_stage3/preference_extractor.py` (stub already there)
- Your training script: `student_scaffold_stage3/train.py` (already exists, implement the TODO)
- Your trained model: `stage3_artifacts/` (tracked by git — commit it as part of your submission; TF-IDF and logistic regression models are typically well under 1MB)
- Additional training data: add examples to `training_data/preference_examples.jsonl`, or create a new file and point `build_extractor()` at it

**Running your training script from the repo root:**
```bash
python -m student_scaffold_stage3.train
# or:
python student_scaffold_stage3/train.py
```

If your classifier uses packages beyond the Python standard library, document how to install them. The grader imports your submitted code, so inference-time dependencies must be available in the grading environment. A scikit-learn classifier that saves a model file under `stage3_artifacts/` is a safe, lightweight choice.

---

## Mini-Stage 0: See Where Stage 2 Fails

**File:** `student_scaffold_stage3/mini_0_observe_extractor.py`

You already ran this above. It tests the Stage-2 keyword rule against a set of phrases and prints which ones it detects correctly and which it misses.

The test set includes three categories of input: direct phrases ("I prefer morning meetings"), paraphrases that express the same intent with different words ("I work best before lunch"), and hard negatives that contain time-of-day words but express the *opposite* of a preference ("Mornings are impossible for me").

**Look for:** which category the keyword rule misses most. Pay attention to the hard negatives — a classifier that simply checks whether "morning" appears in the text will misclassify these, and they appear in the graded eval.

What would it take to correctly handle both "I work best before lunch" (should be `morning`) and "Mornings are impossible for me" (should be `none`)? These two cases are the core challenge your classifier needs to solve.

---

## Mini-Stage 1: Evaluate Your Classifier

**File:** `student_scaffold_stage3/mini_1_predict_preference.py`

**Run:**
```bash
CLIENT=scripted bash launch stage3-mini1
```

This file is complete. It runs your classifier against a fixed held-out diagnostic set and prints accuracy, a confusion matrix, and any mispredictions.

**Before running:**
1. Read the three `ARCHITECTURE.md` sections listed at the top of this document
2. Choose your algorithm and feature representation
3. Write a training script that reads labeled data, fits the model, and saves it to `stage3_artifacts/`
4. Implement `PreferenceExtractor.predict()` and `build_extractor()` in `preference_extractor.py`
5. Train your model and confirm the saved file exists in `stage3_artifacts/`

The starter seed in `training_data/preference_examples.jsonl` has about 5 examples per class — not enough to pass this diagnostic on its own. Running mini-stage 1 on a seed-only classifier will show failures. Fix them by working through this loop:

1. Look at the confusion matrix. Which class has the most errors?
2. Look at the mispredictions. What kind of phrasing is failing — paraphrases you haven't seen, or hard negatives being misclassified?
3. Add **5–10 new examples** that address those gaps. Write them yourself; don't copy the diagnostic cases.
4. Retrain and run mini-stage 1 again.
5. Repeat until accuracy is high.

Aim for **20–30 examples per class** total. Document what you added and why in your checkpoint.

**Things to observe in the output:**
- What is the overall accuracy on the held-out set?
- Which class has the most errors? Are errors concentrated in paraphrases or hard negatives?
- Look at the confidence values for mispredictions. Are the errors low-confidence (uncertain) or high-confidence (confidently wrong)? This distinction matters for choosing your threshold in `agent.py`.

**On generalization vs. fitting to this diagnostic:**

The cases in this mini-stage are visible to you in the file. Don't copy the exact failing sentences into your training data — that's memorizing a visible diagnostic, not learning the pattern.

For each error: what class of phrasing is the model missing? Add several diverse examples of that kind. If "before lunch" fails, add "before noon", "early in the day", "I like to get things done in the morning" and a few more. The goal is to teach the classifier what morning preference *means*, not to make it recognize one specific phrase.

The graded benchmark uses users and phrasings you haven't seen. A classifier that truly generalizes will pass this diagnostic easily. One that was tuned to these 22 cases will likely miss the novel phrasings in the graded eval.

---

## Mini-Stage 2: Connect Your Classifier to the Agent

**File:** `student_scaffold_stage3/mini_2_write_learned_memory.py`

**Prerequisites:** mini-stage 1 runs and your classifier predicts at least some non-`none` labels with reasonable confidence.

**Run:**
```bash
CLIENT=scripted bash launch stage3-mini2
```

You have a working classifier. Now you need to wire it into the scheduling loop: predict at the start of the session, conditionally write to memory, then run the Stage-2 loop unchanged.

The file already calls `self.extractor.predict(session.user_message)` so the pipeline runs before your classifier is tuned. Your job is to replace the starter threshold and write policy with something you can justify: write memory only when the label is `morning` or `afternoon` and the confidence is high enough. The patterns are the same ones you used in Stage 2 — the key change is using `self.extractor.predict` instead of `extract_direct_time_preference`, and passing `prediction.confidence` instead of `1.0`.

What should the `confidence` argument to `runtime.write_memory` be — the classifier's actual confidence, or a fixed value like `1.0`?

<details>
<summary>Answer</summary>

Pass `prediction.confidence`, not `1.0`. Stage 2 used `1.0` because a keyword match is certain — either the phrase is there or it isn't. A trained classifier is not always certain. Storing the actual confidence makes the memory entry honest about its source. Writing `1.0` would hide the uncertainty and make it harder to reason about conflict resolution later (for example, you could build a resolver that trusts a 0.95-confidence entry over a 0.55-confidence one — but only if the stored value reflects the real confidence).
</details>

**Working when** the mini-stage completes with a final response, writes memory for real preference paraphrases, and uses that memory to pick the preferred valid slot.

---

## Mini-Stage 3: Practice the Full Integration (Optional)

**File:** `student_scaffold_stage3/mini_3_learned_memory_loop.py`

**Run:**
```bash
CLIENT=scripted bash launch stage3-mini3
```

A second integration exercise with the same two TODOs as mini-stage 2 but starting from a fresh file. Use it if you want another round of practice before implementing `agent.py`, or skip it if mini-stage 2 felt solid. No new concepts.

---

## When Things Go Wrong

**mini-stage 1 accuracy is low (classifier problem):** look at the confusion matrix. Are errors concentrated on one class? Add 5–10 diverse examples of the failing class and retrain. If hard negatives are being misclassified (e.g., "Mornings are impossible" → `morning`), you need more `none` examples that contain time-of-day words. Don't add the exact failing sentences — add examples of the same *kind* of phrasing.

**`preference_accuracy` is low but mini-stage 1 looks good (integration problem):** the classifier works in isolation but something went wrong in the connection to the agent. Run `bash launch stage3-mini2` and trace the execution: does the classifier run? Does it predict the right label? Does `runtime.write_memory` get called? Does `runtime.search_memory` return the memory in the next session?

**Classifier predicts `none` for everything:** likely a training data imbalance — too many `none` examples relative to `morning`/`afternoon`. Check your class counts. Also confirm your training script is reading the full data file.

**`build_extractor` raises `FileNotFoundError`:** your trained model file is missing from `stage3_artifacts/`. Run your training script first, confirm the file exists, then rerun. Remember to commit the model file — the grader needs it in your submission.

**High confidence on wrong predictions:** the classifier is confidently wrong, which usually means it latched onto a spurious feature (e.g., message length, or the presence of any time word regardless of negation). Add more diverse examples across all classes, especially hard negatives for the misclassified class.

---

## The Final Agent

**File:** `student_scaffold_stage3/agent.py`

**Step 1: Implement the two TODOs**

The scaffold has the same two blocks you filled in mini-stage 2. Implement them using those same patterns.

The one new design decision compared to mini-stage 2: add a named confidence threshold constant at the top of the file and use it in the memory-write condition. Mini-stage 1 gave you data to calibrate this — look at the confidence values your classifier assigned to correct predictions versus errors, and choose a cutoff you can justify. There's no universal right answer; the checkpoint asks you to explain your choice.

Sort the mini-stage 1 predictions by confidence. Find where correct predictions cluster versus where errors appear. Pick a threshold that sits between them. Then validate with `bash launch stage3-eval` — `preference_accuracy` should be non-zero. If it stays at zero, the threshold is too high and no memories are being written; lower it. If `preference_accuracy` is low despite writes happening, the classifier is writing the wrong label — improve your training data.

**Step 2: Evaluate**

```bash
bash launch stage3-eval
```

**Design choices worth thinking through:**

- **Confidence threshold.** What cutoff minimizes wrong writes without filtering out too many correct ones? What did your mini-stage 1 evaluation suggest?

- **Should you keep the Stage-2 rule as a fallback?** If your classifier predicts `none` but the message contains an exact keyword like "afternoon", should you still write memory? There are reasonable arguments both ways — document your decision.

- **What if useful context is inside the note, not the user message?** The current design classifies `session.user_message` before opening any source. But a user's scheduling note might contain preference information. How would you restructure to use that?

Don't hard-code visible phrases, users, dates, or expected slots.

---

## Stage-3 Checkpoint

Fill in this table and the two blanks before submitting.

**Classifier summary:**

| Aspect | Your choice |
|--------|------------|
| Algorithm | |
| Training examples: morning / afternoon / none | &nbsp;&nbsp;&nbsp;/ &nbsp;&nbsp;&nbsp;/ |
| mini-stage 1 overall accuracy | |
| Confidence threshold chosen | |

**Failure case:** from your mini-stage 1 confusion matrix, describe the most common error type and what kinds of training examples you added to address it:

→

**Classifier choice:** local classifier or LLM-as-classifier? One sentence stating your choice and the main reason:

→

---

## Optional Extensions (not graded)

**Fine-tune a small model with LoRA.** Instead of a traditional classifier, fine-tune a small pre-trained language model (e.g., DistilBERT) using low-rank adaptation. This typically generalizes better to novel phrasings because it starts from a model that already understands language. The `peft` and `transformers` libraries are good starting points. Your `build_extractor()` loads the fine-tuned weights and wraps them in the same `PreferenceExtractor` interface — the rest of the agent code doesn't change. If you go this route, document what model you used and how mini-stage 1 accuracy compares to your original classifier.

**Make a more general scheduling agent.** The current agent only handles meeting scheduling. You could extend it to handle reminders, recurring events, or cancellations. The agent loop itself doesn't need to change — tool generality comes from the tools you define and the prompt rules you add.

**Swap in a different tool set.** The same scaffold can support agents outside scheduling: course LMS tools, a task tracker, a code repository API, a document search tool, or a lab inventory database. The agent loop is the same regardless — choose a tool, run it, return the result, repeat. The main design work is deciding which tool outputs are trusted, which actions need deterministic checks, and how to score success.

---

## Optional Next Step: Social Arena

After your Stage 3 agent works, you can enter it in the social arena:

```bash
bash launch social
```

For extra credit, read `student_scaffold_social/CHALLENGE.md` and implement `student_scaffold_social/agent.py`. The social arena uses the same scheduling tasks but adds messier preference cases: preferences inside notes or emails, one-time overrides, and constraints like "mornings are impossible today."

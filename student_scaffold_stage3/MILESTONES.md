# Stage-3 Mini-Stages

Stage 3 has a different workflow from Stages 1 and 2. In those stages you could run mini-stages immediately. Here, mini-stage 1 requires a trained classifier — you have to build it first.

**Before you start — read these three sections of `ARCHITECTURE.md` first (≈8 min total):**
- **"Your Task: Build a Preference Classifier"** — defines the three-class problem (`morning` / `afternoon` / `none`), the required interface (`PreferenceExtractor.predict()` returning a `Prediction` with `.label` and `.confidence`), and the algorithm options. Read this before writing any classifier code.
- **"Why Not Just Ask the LLM?"** — explains why the graded eval penalizes using the LLM as your classifier, even though it works in practice. Understand this before choosing your approach.
- **"Training Data Strategy"** — explains the difference between fitting to the visible diagnostic set (which fails the hidden eval) and building a classifier that generalizes. This is the most common source of grading surprises in Stage 3. Read it before you start collecting examples.

**The order:**
1. Run mini-stage 0 (already complete — shows you the problem).
2. Read `ARCHITECTURE.md` sections above.
3. Implement your classifier in `preference_extractor.py` and write a training script.
4. Train your classifier and save the model to `stage3_artifacts/`.
5. Run mini-stage 1 (evaluates your classifier).
6. Run mini-stage 2 (integrates it with the agent loop).
7. Implement `agent.py`.

**Where to put things:**
- Your classifier: `student_scaffold_stage3/preference_extractor.py` (stub already there)
- Your training script: anywhere inside `student_scaffold_stage3/`, e.g. `train.py`
- Your trained model: `stage3_artifacts/` (tracked by git — commit your trained model as part of your submission; TF-IDF and logistic regression models are typically well under 1MB)
- Your training data: add examples to `training_data/preference_examples.jsonl`, or create a new file and load it from `build_extractor()`

**Running your training script:**
```bash
cd /path/to/course_project
python -m student_scaffold_stage3.train   # if saved as student_scaffold_stage3/train.py
# or just:
python student_scaffold_stage3/train.py
```

---

## Mini-Stage 0: See Where Stage 2 Fails

**File:** `student_scaffold_stage3/mini_0_observe_extractor.py`

**Run:**
```bash
CLIENT=scripted bash launch stage3-mini0
```

**This file is already complete.** Do not edit it — just run it and read the output.

**What it does:** Runs the Stage-2 keyword rule on a set of test cases and prints which ones it detects correctly vs. misses. The test cases include direct phrases, paraphrases, and hard negatives.

**What to observe:**
- Which category (morning, afternoon, none) does the rule miss most?
- The rule contains only a few keyword phrases. Why does "before lunch" escape it?
- Look at the hard negatives at the bottom ("Mornings are impossible for me"). Does the rule correctly return `none` for these, or does the keyword match cause a false positive?

**When this works:** You see a table with EXPECTED / DETECTED / CASE columns and a summary accuracy below it. Some rows show MISS.

**Think about:** The classifier you build must detect the paraphrases the rule misses. But it must also correctly return `none` for the hard negatives — these are the tricky cases to get right.

---

## Mini-Stage 1: Evaluate Your Classifier

**File:** `student_scaffold_stage3/mini_1_predict_preference.py`

**Prerequisites:** You have implemented `PreferenceExtractor` and `build_extractor` in `preference_extractor.py`, and your classifier is trained.

**Run:**
```bash
CLIENT=scripted bash launch stage3-mini1
```

**This file is already complete.** It runs your classifier against a fixed held-out diagnostic set and prints accuracy, a confusion matrix, and any mispredictions.

**Before running, you must:**
1. Read ARCHITECTURE.md sections "Your Task: Build a Preference Classifier", "Why Not Just Ask the LLM?", and "Training Data Strategy".
2. Decide on your algorithm and feature representation. Read the tradeoff discussion.
3. Write a training script that reads your labeled data, fits the model, and saves it to `stage3_artifacts/`. Commit the trained model file — it is tracked by git and is part of your submission.
4. Implement `PreferenceExtractor.predict()` and `build_extractor()` in `preference_extractor.py`.
5. Train your model on the starter seed (`python your_train_script.py` or however you set it up).
6. Then run this mini-stage to see your baseline.

**After running, iterate:**

The starter seed in `training_data/preference_examples.jsonl` is intentionally small — about 5 examples per class. Running mini-1 on a classifier trained only on the starter set will show you failures. That is expected and intentional. Your job is to fix them:

1. Look at the confusion matrix. Which class has the most errors?
2. Look at the mispredictions. What kind of phrasing is failing — paraphrases you haven't seen, hard negatives being misclassified?
3. Add **5–10 new examples** that address those gaps. Write them yourself; do not copy the diagnostic cases.
4. Retrain and run mini-1 again.
5. Repeat until mini-1 accuracy is high.

Aim for **20–30 examples per class** total. Document what you added and why in your reflection.

**What to observe:**
- What is the overall accuracy on the held-out set?
- Which class has the most errors? Are errors concentrated on paraphrases or on hard negatives?
- Look at the confidence values reported for mispredictions. Are errors low-confidence (classifier uncertain) or high-confidence (classifier confidently wrong)?
- What changes to training data or algorithm would fix the worst errors?

**When this works:** The mini-stage prints a confusion matrix and accuracy. With the starter extractor unchanged, it should run but mostly predict `none`. That means the pipeline is working, but the classifier is not useful yet.

**Think about:** What accuracy is good enough? An 80% classifier might write wrong preferences in 20% of sessions. Is that acceptable? What would you rather tune: precision (avoid wrong writes) or recall (catch more preferences)?

**Important — on generalization vs. fitting to this eval:**

The diagnostic cases in this mini-stage are visible to you in the file. Do not copy the exact failing sentences into your training data. That is memorizing a visible diagnostic, not building a classifier.

Here is the reason: the graded benchmark uses users and phrasings you have not seen. A classifier that truly generalizes — by learning what time preference means across varied language — will pass this diagnostic eval easily as a byproduct. A classifier that was tuned specifically to these 22 cases will likely score well here and miss the novel phrasings in the graded test.

When your classifier gets something wrong, ask: *what class of phrasing is my model missing?* Then add several diverse examples of that kind — not the exact sentence that tripped it up. The goal is to teach the classifier a pattern, not a fact.

---

## Mini-Stage 2: Integrate With the Agent Loop

**File:** `student_scaffold_stage3/mini_2_write_learned_memory.py`

**Run:**
```bash
CLIENT=scripted bash launch stage3-mini2
```

**Prerequisites:** mini-stage 1 runs and your classifier predicts at least some non-`none` labels with reasonable confidence.

**Gap this fills:** You have a working classifier. Now you need to connect it to the Stage-2 scheduling loop: predict at the start of the session, conditionally write to memory, then run the loop.

**The concept:** The loop in this file is the Stage-2 memory loop unchanged. The step block at the top replaces the Stage-2 keyword rule:

- **STEP A:** Call `self.extractor.predict(session.user_message)`. If the label is `morning` or `afternoon`, call `runtime.write_memory`. If the label is `none`, skip the write.
- **STEP B:** Same memory search and active preference logic as Stage 2 — already handled below the TODOs.

**Think about it first:** What should the `confidence` argument to `runtime.write_memory` be? Stage 2 always used `1.0` because a keyword match is a certain detection. Is that appropriate here?

<details>
<summary>Answer</summary>

Pass `prediction.confidence`, not `1.0`. The classifier is not always certain. Recording the actual confidence means the memory entry is honest about its source, and you can use that value later (in agent.py) to apply a threshold. Writing `1.0` would hide the uncertainty.
</details>

**Your task:** Make the starter learned-memory block real. The file already calls `self.extractor.predict(session.user_message)` so the starter pipeline can run. After your classifier works, replace the starter threshold/write policy with one you can justify: write memory only when the label is `morning` or `afternoon` and the confidence is high enough. The patterns are the same ones you used in Stage 2 — the key changes are using `self.extractor.predict` instead of `extract_direct_time_preference`, and passing `prediction.confidence` instead of `1.0`.

**What to observe:** With `CLIENT=scripted`, the agent runs the full scheduling loop. If the session message contains a preference paraphrase (check the scenario for user "casey"), the event should be created at the preferred slot. If no preference is detected, the agent falls back to the model's choice.

**When this works:** The mini-stage completes with a final response, writes memory for real preference paraphrases, and uses that memory to pick the preferred valid slot.

---

## Mini-Stage 3: Practice the Full Integration (Optional)

**File:** `student_scaffold_stage3/mini_3_learned_memory_loop.py`

**Run:**
```bash
CLIENT=scripted bash launch stage3-mini3
```

**What it is:** A second integration exercise — same two TODOs as mini_2, but starting from a fresh file. Use it if you want another round of practice before implementing `agent.py`, or skip it if mini_2 felt solid.

The TODOs are identical in structure to mini_2: call `self.extractor.predict`, conditionally write memory, search memory, then run the Stage-2 loop unchanged. If mini_2 worked, this file adds no new concepts.

---

## Debugging Stage 3

Use these when your Stage 3 score is not what you expect.

**mini-stage 1 accuracy is low (classifier problem):** Look at the confusion matrix. Are errors concentrated on one class? Add 5–10 diverse examples of the failing class and retrain. If the error is hard negatives being misclassified (e.g., "Mornings are impossible" classified as `morning`), add more `none` examples with time-of-day words. Do not add the exact failing sentences — add examples of the *kind* of phrasing that is failing.

**`preference_accuracy` is low but mini-stage 1 looks good (integration problem):** The classifier works in isolation but something is wrong with how it connects to the agent. Run `bash launch stage3-mini2` and check the print output — does the classifier run? Does it predict the right label? Does `runtime.write_memory` get called? Does `runtime.search_memory` return the memory in the next session?

**Classifier predicts `none` for everything:** Likely a training data imbalance issue — too many `none` examples relative to `morning`/`afternoon`. Check your class counts. Also check that your training script is reading the full training data file, not a subset.

**`build_extractor` raises `FileNotFoundError`:** Your trained model file is missing from `stage3_artifacts/`. Run your training script first, then confirm the file exists before running the eval. Remember to commit the trained model file — it is tracked by git and should be included in your submission.

**High confidence on wrong predictions:** The classifier is confidently wrong. Usually means the model is relying on spurious features (e.g., message length). Add more diverse examples across all classes, especially hard negatives for the misclassified class.

---

## Final Stage-3 Agent

**File:** `student_scaffold_stage3/agent.py`

**Step 1: Implement the two TODOs**

The scaffold in `agent.py` has the same two STEP blocks you filled in mini-stage 2. Implement them using the same patterns.

The one new design choice compared to mini-stage 2: add a confidence threshold condition to the memory write. Mini-stage 1 gave you data to calibrate this. Look at the confidence values your classifier assigned to correct predictions vs. errors, and choose a cutoff you can justify. Add a named constant at the top of the file and use it in the condition.

**Step 2: Evaluate**

```bash
bash launch stage3-eval
```

**Design choices:**

- **Confidence threshold.** What cutoff minimizes wrong writes without filtering out too many correct ones? What did your mini-stage 1 evaluation suggest? There is no universal right answer — justify your choice.

- **Should you also keep the Stage-2 rule as a fallback?** If your classifier predicts `none` but the message contains an exact keyword like "afternoon", should you still write memory? What would be the argument for and against? Note that if you add the Stage-2 rule as a fallback, Stage-3 is no longer purely learned — document this in your reflection.

- **What if the classifier runs before the tool loop discovers more context?** The current design classifies `session.user_message` before opening the note or email. Is there information inside the note that would help classification? How would you restructure to use it?

Do not hard-code visible phrases, users, dates, or expected slots.

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

**Failure case:** From your mini-stage 1 confusion matrix, describe the most common error type and what kinds of training examples you added to address it:

→

**Classifier choice:** Local classifier or LLM-as-classifier? One sentence stating your choice and the main reason:

→

---

## Optional Extensions (not graded)

These are not required and do not affect your Stage 3 score, but they are worth exploring if you want to go further.

**Fine-tune a small model with LoRA.** Instead of training a traditional classifier, you can fine-tune a pre-trained language model (e.g., a small BERT or DistilBERT variant) using low-rank adaptation (LoRA). This typically generalizes better to novel phrasings because it starts from a model that already understands language. Starting points: the `peft` library from Hugging Face for LoRA support, and `transformers` for loading a pre-trained model. Your `build_extractor()` can load the fine-tuned weights and wrap them in the same `PreferenceExtractor` interface — the rest of the agent code does not change. If you go this route, document what model you used, how many trainable parameters LoRA adds, and how mini-stage 1 accuracy compares to your original classifier.

**Make a general scheduling agent.** The current agent only handles meeting scheduling. You could extend it to handle other types of calendar requests (reminders, recurring events, cancellations) by adding new tools and prompt rules. The agent loop itself does not need to change — tool generality comes from the tools you define and the rules you add.

---

## Optional Next Step: Social Arena

After your Stage 3 agent works, you can enter it in the social arena:

```bash
bash launch social
```

This uses your Stage 3 agent as a baseline. For extra credit, read `student_scaffold_social/CHALLENGE.md` and implement `student_scaffold_social/agent.py`. The social arena still uses scheduling tasks, but it adds messier preference cases: preferences inside notes or emails, one-time overrides, and local constraints like "mornings are impossible today."

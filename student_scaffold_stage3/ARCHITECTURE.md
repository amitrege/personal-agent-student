# Stage-3 Architecture

---

## What You Will Learn in Stage 3

By the end of Stage 3 you will understand:
- How to design, train, and evaluate a **text classifier** for a specific NLP task
- Why **training data quality and diversity** matter more than algorithm choice for small-data settings
- How to use a **confidence threshold** to trade off precision vs. recall in a learned component
- How to integrate a trained model as a **drop-in replacement** for a hand-written rule inside a larger system
- The practical tradeoffs between a local trained classifier and using the LLM directly for classification

---

## How to Use This Document

You do not need to read this end-to-end before writing code.

**Before mini-stage 0:** Read "You Can Already Personalize With Rules" and "What the Rule Gets Wrong" (~3 min).

**Before building your classifier:** Read "Your Task: Build a Preference Classifier", "Why Not Just Ask the LLM?", and "Training Data Strategy" (~8 min).

**Before agent.py:** Read "Where Learning Fits In The Agent" and return to "The Confidence Field" when choosing your threshold.

Everything else is reference.

---

## You Can Already Personalize With Rules

In Stage 2 you added memory to your agent. When a user says "I prefer afternoon meetings," your code detects the phrase, writes it to memory, and on the next session uses that preference to pick a slot. The agent is now personalized.

Stage 3 asks: what happens when the user expresses the same idea with different words?

---

## What the Rule Gets Wrong

The Stage-2 rule in `common.py` checks for a small set of exact phrases:

```python
("afternoon", "later", "late in the day")   # → "afternoon"
("morning", "earlier", "early in the day")  # → "morning"
```

A user who says "I prefer afternoon meetings" matches. But consider:

```text
"I like to wrap things up before lunch."
"The second half of the day works better for me."
"My schedule is usually clear from 2pm onward."
```

None of these phrases appear in the rule. `extract_direct_time_preference` returns `None` for all three. The preference is never written. The agent treats the user as if they had no preference at all, even though the intent is clear.

This is not a flaw in the rule — it is a fundamental limit of keyword matching. The rule works for phrases it was written to catch and fails silently on everything else.

Run `bash launch stage3-mini0` to see exactly where the rule fails before building your classifier.

---

## Your Task: Build a Preference Classifier

Stage 3 asks you to replace the Stage-2 rule with a trained text classifier. The classifier reads a user message and predicts one of three labels:

```text
morning      the message suggests a morning preference
afternoon    the message suggests an afternoon preference
none         the message does not express a scheduling preference
```

You design and implement this classifier. The interface it must satisfy is defined in `preference_extractor.py`:

```python
class PreferenceExtractor:
    def predict(self, text: str) -> Prediction: ...

def build_extractor(settings) -> PreferenceExtractor: ...
```

`Prediction` has two fields:

```python
prediction.label       # "morning", "afternoon", or "none"
prediction.confidence  # float 0.0–1.0
```

`build_extractor` is called once at agent startup. It should load your trained model and return a ready extractor. `predict` is called once per session.

### Algorithm choices

You choose the classifier. A few options with tradeoffs:

**Bag-of-words + Naive Bayes**
Simple to implement, fast, interpretable. Works well when the label correlates with word frequencies. Struggles with negation ("mornings are impossible" shares words with morning-preference examples). Requires very little training data to get off the ground.

**TF-IDF features + logistic regression**
TF-IDF down-weights common words and gives more signal to distinctive terms. Logistic regression gives calibrated probabilities and is easy to evaluate. scikit-learn makes both straightforward. A good step up from plain Naive Bayes.

**Embeddings + classifier head**
Word embeddings (e.g., from a sentence transformer) capture semantic similarity, so "before lunch" and "morning" will have similar representations. Much better generalization. Higher complexity to implement and requires either a pre-trained model or more training data.

**LLM-as-classifier (prompt-based)**
Ask the LLM the question: "Does this message express a morning or afternoon scheduling preference?" This generalizes extremely well. See "Why Not Just Ask the LLM?" for why this is sometimes the wrong choice.

You are not required to use any particular approach. A simpler classifier that is well-tuned and evaluated is better than a complex one used carelessly.

---

## LLM-as-Classifier: Tradeoffs

One legitimate approach is to use the LLM itself as the classifier — add a structured prompt that asks "does this message express a morning or afternoon preference?" and parse the response. Another is to train a local classifier (Naive Bayes, logistic regression, embeddings). Both are valid choices for this task. Here is what each approach gives up and what it gains:

**Local trained classifier**
- *Gains:* Deterministic (same input → same output every time), fast (no model call), independently evaluable on labeled data, easy to iterate by adding training examples
- *Tradeoffs:* Requires labeled data, may struggle with novel phrasing until retrained, no deep semantic understanding without embedding features

**LLM-as-classifier**
- *Gains:* Generalizes well to novel phrasing immediately, can handle nuanced context ("I have a dentist Tuesday morning so Tuesday afternoon is better than usual"), no training data required
- *Tradeoffs:* Adds a model call per session (cost and latency), stochastic (same input might produce different output across calls), harder to evaluate and iterate independently

Neither is universally better. For this task — short, self-contained scheduling messages expressing a simple binary preference — a well-tuned local classifier is a reasonable choice. So is an LLM-based approach. Your checkpoint (see MILESTONES.md) asks you to state your choice and justify it.

If you use the LLM as your classifier, implement it inside `PreferenceExtractor.predict()` so it satisfies the same interface as a local model. Use `prediction.confidence` to reflect the model's stated certainty (or map from its output to a confidence value). The agent loop is identical either way.

---

## Training Data Strategy

Your classifier learns from labeled examples. The quality of your training data matters more than the algorithm you choose.

**Format.** Each example is a JSON line in a `.jsonl` file:

```json
{"text": "I prefer morning meetings.", "label": "morning"}
{"text": "Afternoons work better for me.", "label": "afternoon"}
{"text": "Use the Gmail thread to schedule the meeting.", "label": "none"}
```

A small starter set is provided in `training_data/preference_examples.jsonl`. It has about 5 examples per class, including a few hard negatives. **It is not enough to pass the benchmark on its own.** Its purpose is to show you the format, the three labels, and the kinds of examples that matter — including how a constraint ("my afternoons are packed") differs from a preference. You must collect more examples to make your classifier generalize.

**The collection loop.** The right workflow is iterative:

1. Implement your classifier and train it on the starter set.
2. Run `bash launch stage3-mini1` to see where it fails.
3. For each failure class, ask: *what kind of example would teach a model to handle this?* Write several examples of that kind.
4. Retrain. Run mini-1 again. Repeat until the diagnostic looks good.

Aim for **20–30 examples per class** by the end. More is fine; less usually is not enough.

**Hard negatives.** The seed set includes examples like:

```text
"Mornings are impossible for me this week."     → none
"My afternoons are usually packed."             → none
```

These contain time-of-day words but express the *opposite* of a preference. A classifier that matches keywords will misclassify them. Including hard negatives in training forces the classifier to learn the distinction.

**Diversity.** Similar paraphrases should appear at train time. If your classifier never sees "before lunch" during training, it may not generalize. Aim for variety in sentence structure and vocabulary.

**Volume.** More labeled examples generally help, especially for the `none` class, which has many possible forms. The provided seed is a reasonable starting point. If your classifier is missing a class of phrasing, add several examples of that kind rather than one exact sentence.

**Evaluation.** Hold out at least 20% of your examples for validation. Do not train and evaluate on the same data. Run `bash launch stage3-mini1` after implementing your classifier — it evaluates on a fixed held-out set.

**Generalization is the goal, not eval accuracy.** The held-out cases in mini-stage 1 are visible to you. Do not copy those exact sentences into your training data. That is memorizing a visible diagnostic, not learning the task. The final benchmark uses novel users with novel phrasing you have not seen. A classifier that truly learns what "morning preference" and "afternoon preference" mean — through diverse training examples and the right feature representation — will score well on the mini-stage eval as a natural consequence. A classifier tuned to that eval but not to the underlying signal will fail on genuinely new inputs.

When your classifier gets something wrong in mini-stage 1, ask: "what kind of example would teach a model to handle this class of input?" — not "how do I add this exact sentence to my training set."

---

## The Confidence Field

`prediction.confidence` is how certain the classifier is about its predicted label, not how certain the user is about their preference.

The confidence field matters because you use it to decide whether to write to memory. The right policy:

```python
if prediction.label in {"morning", "afternoon"} and prediction.confidence >= THRESHOLD:
    runtime.write_memory(...)
```

Two failure modes to calibrate against:

- **Threshold too low:** every non-`none` prediction writes memory, including low-confidence guesses. "Mornings are impossible for me" classified as `morning` at 0.3 confidence would write the wrong preference.

- **Threshold too high:** correctly classified paraphrases are filtered out because the classifier assigns moderate confidence. A user's real preference goes undetected.

Use the evaluation output from mini-stage 1 to choose your threshold. Look at what confidence values your classifier assigns to correct predictions vs. errors.

---

## Where Learning Fits In The Agent

The Stage-3 agent is the Stage-2 agent with one substitution at the top of `run_session`:

```text
Stage 2:
    preference = extract_direct_time_preference(session.user_message)
    if preference is not None:
        runtime.write_memory(...)

Stage 3:
    prediction = self.extractor.predict(session.user_message)
    if prediction.label in {"morning", "afternoon"} and prediction.confidence >= THRESHOLD:
        runtime.write_memory(
            key="preferred_time_window",
            value=prediction.label,
            evidence=session.user_message,
            confidence=prediction.confidence,  # ← pass the classifier's confidence, not 1.0
        )
```

The memory search, slot choice, and full tool loop that follow are exactly the same as Stage 2. You are replacing only the memory *writer*. If the classifier predicts `"none"` or confidence is below threshold, the agent behaves exactly like the Stage-2 agent with no detected preference.

---

## What To Avoid

**Do not use the Stage-2 keyword rule as a substitute.** The point of Stage 3 is to replace the rule with a trained component. Using `extract_direct_time_preference` as a fallback re-introduces the Stage-2 limitation. If you want a hybrid, discuss it in your reflection.

**Do not hard-code phrases from the visible sessions.** Hidden test sessions use paraphrases not in the visible data. A rule like `if "second half" in text` is back to the Stage-2 problem.

**Do not let learned memory override the calendar.** Memory still only chooses among confirmed-free slots. The same constraint as Stage 2 — unchanged in Stage 3.

**Do not train and evaluate on the same data.** Hold out examples before training. Report results on the held-out set, not the training set.

---

## Next Step

Open `MILESTONES.md`. It walks you through the mini-stages, then describes the design choices in the final agent.

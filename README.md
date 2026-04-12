# Personal Scheduling Agent — Course Project

You are building a personalized scheduling assistant. By the end of the project you will have an agent that can read a user's notes and emails, create calendar events, remember each user's scheduling preferences across conversations, and apply those preferences using a classifier you trained yourself.

This project is a scheduling-specific version of a more general tool-using agent scaffold. The same loop you build here — ask a model what to do next, run the requested tool, feed the result back, and stop when the task is complete — could be reused with many other tools. For example, a similar agent could search a course LMS, update a task tracker, query a lab inventory system, summarize files, create GitHub issues, or coordinate travel bookings. We focus on notes, email, memory, and calendar tools so the course project has a concrete task and a measurable benchmark, but extending the scaffold to new tools is a natural next project.

---

## What You Are Building

The project has three required stages and one optional social arena. Each stage keeps everything from the previous one and adds one new capability:

| Stage | What it adds | New files you write |
|-------|-------------|---------------------|
| **1 — Tool-use baseline** | Agent loop: read notes/emails, find free slots, create calendar events | `agent.py`, `prompts.py` |
| **2 — Memory** | Preferences persist across sessions; agent picks the user's preferred slot | `agent.py` (extended from Stage 1) |
| **3 — Learned component** | Classifier replaces keyword rule; catches paraphrases the rule misses | `preference_extractor.py`, trained model, `agent.py` (extended from Stage 2) |
| **Social arena (extra credit)** | Harder preference cases; multi-agent competition for simulated users | `student_scaffold_social/agent.py` |

**Stage 1 — Tool-use baseline**
An agent that handles one scheduling request at a time. The user says "schedule the meeting from my note titled X" — your agent finds the note, opens it, extracts the title, date, duration, and attendees, finds a free slot, and creates the calendar event. Each session is independent.

**Stage 2 — Memory-based personalization**
The same agent, now with persistent memory. When a user says "I prefer afternoon meetings," your agent stores that preference and uses it in later sessions to pick slots the user will actually want.

**Stage 3 — Learned component**
Stage 2 only catches direct phrases like "I prefer mornings." Stage 3 replaces the keyword rule with a classifier you design and train, so it also catches paraphrases like "before lunch" or "the second half of the day works better for me."

**Social arena (extra credit)**
Your final Stage 3 agent can enter an arena of simulated users. The arena scores how well it schedules for users whose preferences appear across multiple conversations. A working Stage 3 agent can run here as a baseline for comparison only. Extra credit starts when you build a stronger social version that beats that baseline on harder cases: preferences inside notes or emails, one-time overrides, and messages like "mornings are impossible today."

---

## Getting Started

Open a terminal in this folder before running commands.

Use Python 3.11 or newer. The starter framework uses only the Python standard library, so you do not need to install extra packages before running the mini-stages or visible benchmarks. If you choose to use extra packages for your Stage 3 classifier, make sure your submitted repo documents them and can be run in the grading environment.

### 1. Run the no-model checks first

These commands use the scripted client, so they do not need Colab yet:

```bash
CLIENT=scripted bash launch doctor
CLIENT=scripted bash launch mini0
CLIENT=scripted bash launch grade
```

`doctor_status=ok` means the command runner is working. `mini0` prints the available tools and prompt context. `grade` prints your visible grade estimate across the three stages. With the starter code unchanged, the visible grade should be 0 because Stage 1, Stage 2 memory, and Stage 3 learned memory are not implemented yet.

The student distribution does not include a separate `pytest` test suite. Use the `launch` commands as your checks: the mini-stage commands help you learn one piece at a time, and the eval/grade commands show benchmark scores. Run `bash launch help` to list the available commands.

### 2. Set up the model

Upload `personal_agent_colab_server.ipynb` to Google Colab and click **Run all**. It starts an LLM server and prints connection details. Copy the printed block into a file called `.env.colab` inside this folder.

### 3. Verify the Colab connection

```bash
bash launch doctor
```

You should see `doctor_status=ok` and the Colab model name. If not, check that your Colab runtime is still running and the `.env.colab` file is saved in this folder. After that, `bash launch grade` uses the Colab-backed model by default.

### 4. Start Stage 1

Read `student_scaffold/ARCHITECTURE.md` — it explains what an agent is and walks through the key objects you will use. Then open `student_scaffold/MILESTONES.md` for the step-by-step coding sequence.

**Stage-to-stage progression:** Each stage has its own scaffold directory with a fresh `agent.py`. Stage 2 asks you to copy your Stage-1 `run_session` into `student_scaffold_stage2/agent.py` and extend it. Stage 3 asks you to copy your Stage-2 logic into `student_scaffold_stage3/agent.py` and swap in the classifier. You do not need to modify earlier stages once you move on.

---

## Directory Guide

```
.
├── student_scaffold/          ← Stage 1: your files
│   ├── ARCHITECTURE.md        ←   start here for Stage 1
│   ├── MILESTONES.md          ←   step-by-step coding guide
│   ├── agent.py               ←   main deliverable for Stage 1
│   ├── prompts.py             ←   your prompt rules (also a deliverable)
│   └── mini_*.py              ←   practice files, one concept each
│
├── student_scaffold_stage2/   ← Stage 2: your files
│   ├── ARCHITECTURE.md        ←   start here for Stage 2
│   ├── MILESTONES.md
│   ├── agent.py               ←   main deliverable for Stage 2
│   └── ...
│
├── student_scaffold_stage3/   ← Stage 3: your files
│   ├── ARCHITECTURE.md        ←   start here for Stage 3
│   ├── MILESTONES.md
│   ├── preference_extractor.py ←  implement your classifier here
│   ├── agent.py               ←   main deliverable for Stage 3
│   └── ...
│
├── student_scaffold_social/   ← Social arena (extra credit)
│   ├── CHALLENGE.md           ←   read this to understand the arena
│   └── agent.py               ←   optional stronger social agent
│
├── training_data/             ← Seed training data for Stage 3
│   └── preference_examples.jsonl
│
├── stage3_artifacts/          ← Where trained Stage 3 models go (commit these)
│
├── src/course_project/        ← Framework code (do not edit)
│   ├── student_api.py         ←   StudentRuntime and StudentAgent
│   ├── worlds/                ←   calendar, notes, email tools
│   └── ...
│
├── personal_agent_colab_server.ipynb  ← upload to Colab
└── launch                     ← main command runner
```

Most of your code goes in the `student_scaffold*/` directories. In Stage 3, you may also add training examples under `training_data/` and save trained models under `stage3_artifacts/`. Everything in `src/course_project/` is the benchmark framework — do not modify it.

---

## Visible Test Cases

The visible benchmark cases are included so you can inspect what the grader is checking:

| Area | Visible case file |
|---|---|
| Stage 1 | `src/course_project/scenarios/tool_use_stage_v1/scenario.json` |
| Stage 2 | `src/course_project/scenarios/memory_stage_v1/scenario.json` |
| Stage 3 | `src/course_project/scenarios/learned_memory_stage_v1/scenario.json` |
| Social arena | `src/course_project/scenarios/social_market_v1/scenario.json` |

Each file lists the users, notes, email threads, session prompts, and expected outcomes for the visible benchmark. Use these files to understand the task and debug failures, but do not hard-code user names, note titles, dates, phrasings, or expected slots. Hidden grading cases use different cases.

---

## Visible and Hidden Checks

The commands below are visible practice benchmarks. Use them to debug and estimate progress, but a `suite_score` of 100 on the visible benchmark does not guarantee full credit. Grading may also use hidden users, hidden note/email contents, and hidden preference phrasings that test whether your agent generalized instead of fitting only the visible cases.

For the social arena, the visible arena is a practice leaderboard. Extra credit is based on a hidden arena with broader preference patterns, so use visible scores as a debugging signal rather than as a guarantee.

To check your visible grade estimate as you go:

```bash
bash launch grade
```

This runs the visible Stage 1, Stage 2, and Stage 3 benchmarks and reports:

```
visible_grade = 0.40 * stage1_grade_score + 0.25 * stage2_grade_score + 0.35 * stage3_grade_score
```

Equivalently, Stage 1 is worth 40 points, Stage 2 is worth 25 points, and Stage 3 is worth 35 points. For Stage 1, `grade_score` is the visible `suite_score`. For Stages 2 and 3, `grade_score` also requires the stage-specific memory and preference metrics: it is `min(suite_score, 100 * preference_accuracy, 100 * memory_accuracy)`. This means Stage 2 earns 0 grade points until you implement memory, even if a Stage-1-style loop can still schedule some events. It also means Stage 3 earns 0 grade points until you implement the learned memory component, even if the starter Stage 3 scaffold can still schedule some events.

When an eval score is lower than expected, rerun the debug version to see the visible cases that failed:

```bash
bash launch eval-debug
bash launch stage2-eval-debug
bash launch stage3-eval-debug
```

The debug output includes each failed session's user message, referenced artifact, expected event fields, actual `calendar.create_event` result if any, tool sequence, run directory, and expected/stored memory entries when memory is part of the stage. It is a debugging view of the visible benchmark only; hidden grading cases are still not distributed.

---

## Stage 1 Commands

```bash
# Learn the building blocks (use scripted client — no real model needed)
CLIENT=scripted bash launch mini0
CLIENT=scripted bash launch mini1
CLIENT=scripted bash launch mini2
CLIENT=scripted bash launch mini3
CLIENT=scripted bash launch mini4
CLIENT=scripted bash launch mini5
CLIENT=local   bash launch mini6   # requires real model

# Test your agent on one user
bash launch run alex

# Run the full Stage 1 benchmark
bash launch eval
```

Your Stage 1 grade is based directly on these two scores. A `suite_score` of 100 and `artifact_read_rate` of 1.0 are the targets; partial scores are partial credit. If you see a lower score, check the per-session breakdown in the output — it will show you exactly which field was wrong (title, attendees, time) or whether the artifact was not read before the event was created. Occasional failures on edge cases with a real model (score in the 90s) usually point to a specific gap in your prompt rules or error handling, not random noise.

The grader expects the event fields from the note or email. Title and attendee matching ignores capitalization and extra spaces, but it does not accept extra words such as `Meeting: Lab planning sync` when the source title is `Lab planning sync`. `artifact_read_rate` only checks whether you opened the referenced source before creating the event; `suite_score` is what checks whether you extracted and scheduled the event correctly.

---

## Stage 2 Commands

```bash
# Learn the memory building blocks
CLIENT=scripted bash launch stage2-mini0
CLIENT=scripted bash launch stage2-mini1
CLIENT=scripted bash launch stage2-mini2
CLIENT=scripted bash launch stage2-mini3
CLIENT=scripted bash launch stage2-mini4

# Test your Stage 2 agent
STUDENT_AGENT_MODULE=student_scaffold_stage2.agent SCENARIO=memory_stage_v1 bash launch run alex

# Run the full Stage 2 benchmark
bash launch stage2-eval
```

Your Stage 2 benchmark reports three important scores: `suite_score`, `preference_accuracy`, and `memory_accuracy`. All three matter for Stage 2 credit; `bash launch grade` uses the weakest of those three as the Stage 2 `grade_score`. If `preference_accuracy` is low, the detailed output will show which sessions picked the wrong slot and why. If `memory_accuracy` is low, check whether your agent writes memory when it detects a preference and reads it in the next session.

---

## Stage 3 Commands

Stage 3 requires you to build and train a classifier before running the mini-stages. See `student_scaffold_stage3/ARCHITECTURE.md` for guidance on what to build.

```bash
# Observe where Stage 2 fails (no classifier needed yet)
CLIENT=scripted bash launch stage3-mini0

# After implementing and training your classifier:
CLIENT=scripted bash launch stage3-mini1   # evaluate your classifier
CLIENT=scripted bash launch stage3-mini2   # integrate with the loop

# Run the full Stage 3 benchmark
bash launch stage3-eval
```

Your Stage 3 benchmark reports the same three important scores as Stage 2, but evaluated on novel paraphrases the keyword rule cannot catch. All three matter for Stage 3 credit; `bash launch grade` uses the weakest of those three as the Stage 3 `grade_score`. If accuracy is low, run `bash launch stage3-mini1` to see how your classifier is performing and which cases it misses — fix those first before debugging the agent integration.

---

## Social Arena Commands (extra credit)

```bash
# Run your Stage 3 agent in the arena as a baseline for comparison
bash launch social

# Run your optional social-arena agent instead
SOCIAL_AGENT_MODULE=student_scaffold_social.agent bash launch social
```

The first command uses `student_scaffold_stage3.agent`, so it should work after your Stage 3 agent works. It does not earn extra credit by itself. For extra credit, implement `student_scaffold_social/agent.py` and run the second command. See `student_scaffold_social/CHALLENGE.md` for tactics and open-ended strategy ideas.

---

## Provided Helpers

Each stage's `common.py` provides helper functions already imported into the mini-stage and agent files. You do not need to implement these — they are part of the framework.

**Available in all stages (from `student_scaffold/common.py`):**

| Helper | What it does |
|--------|-------------|
| `build_system_prompt(runtime)` | Assembles the full system prompt from benchmark rules + your `EXTRA_RULES` |
| `assistant_message(response)` | Wraps a model response into a messages list entry |
| `tool_result_message(tool_name, result)` | Wraps a tool result into a messages list entry |

**Added in Stage 2 (from `student_scaffold_stage2/common.py`):**

| Helper | What it does |
|--------|-------------|
| `extract_direct_time_preference(text)` | Keyword rule: returns `"morning"`, `"afternoon"`, or `None` |
| `latest_time_window(memories)` | Returns the most recent valid preference from a memory list |
| `choose_preferred_slot(slots, preference)` | Picks the best slot given a preference; never invents a slot |

**Stage 3 (from `student_scaffold_stage3/preference_extractor.py`):**
You implement `PreferenceExtractor` and `build_extractor()` here. The interface is defined — see the file.

---

## Common Questions

**Why `CLIENT=scripted`?**
The scripted client replaces the real LLM with a fast, deterministic one. Use it while learning the code path — it runs instantly without hitting the Colab server. Switch to `CLIENT=local` (or just `bash launch ...` which defaults to local) once you are ready to test with a real model.

**Why do the mini-stages score 0 on the benchmark?**
They are not supposed to produce correct schedules — they each demonstrate one concept and return early. Only `agent.py` is graded.

**Where do I put my Stage 3 training script?**
Anywhere inside `student_scaffold_stage3/`. A common pattern is to create `student_scaffold_stage3/train.py`. Save the trained model to `stage3_artifacts/` and commit it — it is tracked by git and is part of your submission. Load it in `build_extractor()`.

**The Colab runtime timed out.**
Reconnect and re-run the notebook. The URL in `.env.colab` changes — copy the new block.

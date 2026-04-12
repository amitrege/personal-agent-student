# Personal Scheduling Agent — Course Project

You are building a personalized scheduling assistant that reads notes and emails, creates calendar events, and remembers each user's scheduling preferences. The loop you build — ask a model what to do next, run the requested tool, feed the result back, repeat — is the foundational pattern for agentic AI systems.

---

## The Three Required Stages

| Stage | What it adds | What you implement |
|-------|-------------|---------------------|
| **1 — Tool-use baseline** | Agent loop: read notes/emails, find free slots, create events | `agent.py`, `prompts.py` |
| **2 — Memory** | Preferences persist across sessions; agent picks the preferred slot | `agent.py` extended from Stage 1 |
| **3 — Learned component** | Trained classifier replaces keyword rule; catches paraphrases | `preference_extractor.py`, trained model, `agent.py` extended from Stage 2 |
| **Social arena** | Harder preference cases; multi-agent competition *(extra credit)* | `student_scaffold_social/agent.py` |

Each stage builds on the previous one. Stage 2 starts from your Stage 1 agent; Stage 3 starts from Stage 2.

---

## Start Here

Open a terminal in this folder. Python 3.11+ required; no extra packages needed until Stage 3.

**Step 1 — Run these now (no Colab needed):**

```bash
CLIENT=scripted bash launch doctor   # check the repo is set up correctly
CLIENT=scripted bash launch mini0    # see the tools and prompt your agent will use
CLIENT=scripted bash launch grade    # confirm grade is 0 with starter code
```

`doctor_status=ok` means the setup is working. `mini0` prints the available tools and the system prompt. Grade will be 0 — nothing is implemented yet.

**Step 2 — Set up the model:**

Upload `personal_agent_colab_server.ipynb` to Google Colab and click **Run all**. Copy the printed connection block into a file called `.env.colab` in this folder, then verify:

```bash
bash launch doctor   # should show doctor_status=ok and the model name
```

If it doesn't, check that your Colab runtime is still running and `.env.colab` is saved in this folder. The URL changes each time you restart Colab — copy the new block when that happens.

**Step 3 — Open the Stage 1 guide:**

→ **`student_scaffold/ARCHITECTURE.md`** — what an agent is and the three objects you'll use
→ **`student_scaffold/MILESTONES.md`** — step-by-step coding sequence with mini-stages

Each subsequent stage has its own `ARCHITECTURE.md` and `MILESTONES.md` in its directory. The reference material below is there when you need it; you won't need most of it on first read.

---

## Reference

### Directory Guide

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
│   ├── train.py               ←   training script (implement and run this first)
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

Your code goes in the `student_scaffold*/` directories. In Stage 3, add training examples under `training_data/` and save trained models under `stage3_artifacts/`. Do not modify anything in `src/course_project/`.

---

### Commands

**Utility:**

| Command | Use it when |
|---|---|
| `bash launch help` | You want to see all available commands. |
| `CLIENT=scripted bash launch doctor` | You want to check the repo works without Colab. |
| `bash launch doctor` | You want to check the Colab-backed model is reachable. |
| `bash launch grade` | You want a visible grade estimate across all three stages. |

**Stage 1:**

```bash
CLIENT=scripted bash launch mini0    # observe tools and prompt
CLIENT=scripted bash launch mini1    # make the first model call
CLIENT=scripted bash launch mini2    # parse the model's response
CLIENT=scripted bash launch mini3    # execute one tool
CLIENT=scripted bash launch mini4    # complete one round trip
CLIENT=scripted bash launch mini5    # build the loop
CLIENT=local   bash launch mini6    # watch with no rules (requires real model)
bash launch run alex                 # test your agent on one user
bash launch eval                     # full Stage 1 benchmark
bash launch eval-debug               # see failed cases
```

**Stage 2:**

```bash
CLIENT=scripted bash launch stage2-mini0   # observe memory
CLIENT=scripted bash launch stage2-mini1   # write a memory
CLIENT=scripted bash launch stage2-mini2   # read memory across sessions
CLIENT=scripted bash launch stage2-mini3   # choose a slot from memory
CLIENT=scripted bash launch stage2-mini4   # memory inside the tool loop
STUDENT_AGENT_MODULE=student_scaffold_stage2.agent SCENARIO=memory_stage_v1 bash launch run alex
bash launch stage2-eval
bash launch stage2-eval-debug
```

**Stage 3:**

```bash
CLIENT=scripted bash launch stage3-mini0   # see where Stage 2 fails
CLIENT=scripted bash launch stage3-mini1   # evaluate your classifier
CLIENT=scripted bash launch stage3-mini2   # connect classifier to the loop
bash launch stage3-eval
bash launch stage3-eval-debug
```

**Social arena (extra credit):**

```bash
bash launch social                                                    # run Stage 3 agent as baseline
SOCIAL_AGENT_MODULE=student_scaffold_social.agent bash launch social  # run your social agent
```

---

### Runtime Tools

These are the tools your agent can call during a session:

| Tool | What it does |
|---|---|
| `simple_note.search_notes` | Search note titles and bodies. |
| `simple_note.show_note` | Open one note by `note_id`. |
| `gmail.show_inbox_threads` | Search email thread subjects and recent message text. |
| `gmail.show_thread` | Open one email thread by `email_thread_id`. |
| `calendar.find_free_slots` | Return available start times for the task date and duration. |
| `calendar.create_event` | Create a calendar event with title, date, start time, duration, and attendees. |
| `calendar.list_events` | List calendar events, optionally for one date. |

Example flow for "Use my SimpleNote note titled 'Monday planning brief' to schedule the meeting":

1. `simple_note.search_notes` — find the note by title
2. `simple_note.show_note` — open it and read title, date, duration, attendees
3. `calendar.find_free_slots` — get available times for that date and duration
4. `calendar.create_event` — create the event with fields from the note
5. `runtime.finish(...)` — return the final response

Your loop executes whatever tool the model requests. Do not hard-code note titles or dates — the model drives that logic from the prompt and tool results.

---

### Grading

```bash
bash launch grade
```

Reports:

```
visible_grade = 0.40 * stage1_grade_score + 0.25 * stage2_grade_score + 0.35 * stage3_grade_score
```

Stage 1 is worth 40 points, Stage 2 is 25, Stage 3 is 35. For Stage 1, `grade_score` equals the visible `suite_score`. For Stages 2 and 3, `grade_score` is `min(suite_score, 100 * preference_accuracy, 100 * memory_accuracy)` — all three metrics must be non-zero to earn credit.

A `suite_score` of 100 on the visible benchmark does not guarantee full credit. Grading also uses hidden users, hidden note/email contents, and hidden preference phrasings that test generalization. Treat visible scores as a debugging signal, not a ceiling.

When a score is lower than expected, run the debug variant to see which visible cases failed:

```bash
bash launch eval-debug
bash launch stage2-eval-debug
bash launch stage3-eval-debug
```

---

### Visible Test Cases

The visible benchmark inputs are included so you can inspect what the grader checks:

| Stage | File |
|---|---|
| Stage 1 | `src/course_project/scenarios/tool_use_stage_v1/scenario.json` |
| Stage 2 | `src/course_project/scenarios/memory_stage_v1/scenario.json` |
| Stage 3 | `src/course_project/scenarios/learned_memory_stage_v1/scenario.json` |
| Social arena | `src/course_project/scenarios/social_market_v1/scenario.json` |

Each file lists the users, notes, email threads, session prompts, and expected outcomes. Do not hard-code user names, note titles, dates, phrasings, or expected slots — hidden grading cases use different values.

---

### Provided Helpers

Each stage's `common.py` provides helper functions already imported into the mini-stage and agent files. Do not reimplement them.

**All stages (`student_scaffold/common.py`):**

| Helper | What it does |
|--------|-------------|
| `build_system_prompt(runtime)` | Assembles the full system prompt from benchmark rules + your `EXTRA_RULES` |
| `assistant_message(response)` | Wraps a model response into a messages list entry |
| `tool_result_message(tool_name, result)` | Wraps a tool result into a messages list entry |

**Stage 2 adds (`student_scaffold_stage2/common.py`):**

| Helper | What it does |
|--------|-------------|
| `extract_direct_time_preference(text)` | Keyword rule: returns `"morning"`, `"afternoon"`, or `None` |
| `latest_time_window(memories)` | Returns the most recent valid preference from a memory list |
| `choose_preferred_slot(slots, preference)` | Picks the best slot given a preference; never invents a slot |

**Stage 3:** Implement `PreferenceExtractor` and `build_extractor()` in `student_scaffold_stage3/preference_extractor.py`. The interface is defined in that file.

---

### Common Questions

**Why `CLIENT=scripted`?**
The scripted client replaces the real LLM with a fast, deterministic one. It runs instantly without hitting Colab. Switch to `CLIENT=local` (or just `bash launch ...`, which defaults to local) when you're ready to test with a real model.

**Why do the mini-stages score 0 on the benchmark?**
They each demonstrate one concept and return early — they are not meant to produce correct schedules. Only `agent.py` is graded.

**Where do I put my Stage 3 training script?**
Use the existing `student_scaffold_stage3/train.py` — it has the data-loading and model-saving boilerplate already set up. Save the trained model to `stage3_artifacts/` and commit it — it is tracked by git and is part of your submission. Load it in `build_extractor()`.

**The Colab runtime timed out.**
Reconnect and re-run the notebook. The URL in `.env.colab` changes — copy the new block.

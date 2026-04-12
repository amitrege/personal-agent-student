# Stage-1 Mini-Stages

Do not start by editing `agent.py`. Work through these mini-stages first. Each one adds one concept. By Mini-Stage 5 you will have seen every building block the full agent uses — then `agent.py` is those blocks in a loop, with two additions.

**Before you start — read these three sections of `ARCHITECTURE.md` first (≈5 min total):**
- **"What an Agent Is"** — explains the loop pattern your code must implement: model call → parse action → run tool → repeat. Every mini-stage is one piece of this loop.
- **"The Three Main Objects"** — shows the `runtime`, `session`, and `response` objects you will use throughout. Know what `runtime.complete()`, `runtime.call_tool()`, and `runtime.finish()` do before writing any code.
- **"The JSON Response Format"** — the model always replies with `{"tool_call": ..., "final_response": ...}`. Your code branches on these two fields. Skim this so the format is not a surprise when you see it in mini-stage 2.

Use `CLIENT=scripted` for all mini-stages through mini_5. That gives you a deterministic, fast response so you can learn the code path without waiting on a real model. Switch to the real model for mini_6 and the final agent.

---

## Mini-Stage 0: Observe the System

**File:** `student_scaffold/mini_0_finish.py`

**Run:**
```bash
CLIENT=scripted bash launch mini0
```

**This file is already complete.** Do not edit it — just run it and read the output.

**What it does:** Prints three things before returning:
1. The user message (`session.user_message`) — what the user asked
2. The available tools — every tool your agent can call, with parameter names
3. The full system prompt — the instructions the model receives, including tool descriptions and response format

**What to observe:**
- Write down the tool names. You will use them when writing `prompts.py` rules.
- Read the system prompt end-to-end. Notice the JSON response format the model is expected to follow.
- Note what fields `calendar.create_event` requires — the grader checks these.

**When this works:** You will see the user message, a list of 7 tool names (two note tools, two email tools, three calendar tools), and the full system prompt ending with the `tool_call` / `final_response` JSON format block. Last line: `Exploration complete.`

**Think about:** Look at the tool list. Given the user message, which tool would you call first? What argument would you pass?

<details>
<summary>Answer</summary>

The user message says "Use my SimpleNote note titled 'Monday planning brief'..." so the first tool is `simple_note.search_notes` with `query="Monday planning brief"`. That gives you a list of matching notes. You then need the note's ID to call `simple_note.show_note` and get the full content. The model figures this out — your job is to run the tools it requests.
</details>

---

## Mini-Stage 1: Call the Model Once

**File:** `student_scaffold/mini_1_model_call.py`

**Run:**
```bash
CLIENT=scripted bash launch mini1
```

**Gap this fills:** Mini-Stage 0 returns a hardcoded string. You need to actually ask the model what to do with the user's request.

**The concept:** `runtime.complete(messages, require_json)` sends the conversation history to the model and returns a response object. You pass the system prompt as the first message, followed by the user messages. `require_json=True` tells the model it must reply with valid JSON so your code can parse it later.

**Think about it first:** You have the user message in `messages` and the system instructions in `system_prompt`. What does the model need to receive before it can suggest a first action? What format does that input need to be in?

<details>
<summary>Answer</summary>

The model needs both the instructions (system prompt) and the user's request in the `messages` list. The system prompt goes first as `{"role": "system", "content": system_prompt}`, then the user message follows. This is the same shape as a raw OpenAI API call — `runtime.complete()` just wraps it with a cleaner interface and routes to whichever client is configured.
</details>

**Your task:** Replace `response = ...` with a call to `runtime.complete`. Look up the signature in ARCHITECTURE.md under "The Three Main Objects — runtime". You have the user message and the system prompt — make sure the model receives both. Pay attention to how the messages list should be structured.

**What to observe:** With `CLIENT=scripted`, the output should end with a JSON string containing a `tool_call`. Add a `print(response.content)` before the return to confirm.

**When this works:** The last line of output is a JSON string with `tool_call` and `final_response` keys. If you see a Python exception, re-read the call signature in ARCHITECTURE.md — note that all arguments are keyword-only.

---

## Mini-Stage 2: Parse the Model Action

**File:** `student_scaffold/mini_2_parse_action.py`

**Run:**
```bash
CLIENT=scripted bash launch mini2
```

**Gap this fills:** `response.content` is a raw string — you cannot write `if response.content['tool_call']`. You need a Python dict.

**The concept:** `parse_action(content)` turns the model's JSON string into a dict with two useful keys:
- `action['tool_call']` — a dict `{"name": ..., "arguments": {...}}` if the model wants a tool run; `None` if not
- `action['final_response']` — a non-empty string if the model is finished; `""` if not

Every agent turn branches on exactly these two fields. Either there is a tool to run, or there is a final answer to return.

**Think about it first:** `response.content` is the string `'{"tool_call": {"name": "simple_note.search_notes", ...}, "final_response": ""}'`. What do you need to do to it before you can write `if action.get("tool_call")`?

<details>
<summary>Answer</summary>

Parse it. A string can't be subscripted like a dict. `parse_action()` calls `json.loads()` under the hood and normalizes the result — it handles aliases and edge cases so you don't have to. The result is a plain Python dict you can branch on.
</details>

**Your task:** Replace `action = ...`. The function `parse_action` is already imported at the top of the file. Look at what you have (the model's response object) and what `parse_action` expects as input.

**What to observe:** Print `action`. It should be a dict with `tool_call` and `final_response` keys. Check what fields are inside `action['tool_call']` — you will need them next.

**When this works:** Printing `action` produces a dict. If you get a `TypeError` or `None`, check what you are passing to `parse_action`.

---

## Mini-Stage 3: Call One Tool

**File:** `student_scaffold/mini_3_one_tool.py`

**Run:**
```bash
CLIENT=scripted bash launch mini3
```

**Gap this fills:** You know which tool the model wants, but the model cannot run it. Your Python code must execute the tool.

**The concept:** `runtime.call_tool(tool_name, arguments, turn_index)` runs the named tool in the benchmark world and returns three values: the tool name used, the arguments used, and the result. The result is real data — a list of notes, a note's full content, available time slots, a calendar confirmation, etc.

**Think about it first:** You have `action['tool_call']['name']` and `action['tool_call']['arguments']`. What needs to happen before the model can use this information?

<details>
<summary>Answer</summary>

Your Python code calls the tool and gets the result. The model lives inside `runtime.complete()` — it produces text. It has no ability to reach into a file system or calendar API. Only your code can do that. Once you have the result, you need to get it back into the conversation so the model can see it — that's the next mini-stage.
</details>

**Your task:** Replace the sentinel with a call to `runtime.call_tool`. You have the action dict from mini-stage 2 — pull out the tool name and arguments and pass them through. Look up the signature in ARCHITECTURE.md.

**What to observe:** Print `result`. You should see real data from the benchmark world — a list of note summaries or similar. This is what the model needs to decide its next step.

**When this works:** `result` contains benchmark data (not `None`). If you get a `KeyError` or `TypeError`, re-read how `call_tool` expects its arguments to be passed.

---

## Mini-Stage 4: Send the Tool Result Back

**File:** `student_scaffold/mini_4_one_round_trip.py`

**Run:**
```bash
CLIENT=scripted bash launch mini4
```

**Gap this fills:** The tool result is in your Python variable. The model does not know about it yet.

**The concept:** After a tool call, append the result to `messages` using `tool_result_message(tool_name, result)`, then call `runtime.complete()` again with the updated messages. This is one complete "round trip": model asks → tool runs → model sees result. The full agent is many round trips in a loop.

**Think about it first:** After the tool runs, you have the result in a Python variable. How does the model find out what the tool returned?

<details>
<summary>Answer</summary>

You add the result to `messages` using `tool_result_message()`, which formats it as a user-role message the model can read. Then you call `runtime.complete()` again with the updated messages list. The model sees the tool result and decides what to do next. If you skip adding the result to `messages`, the model calls the same tool again — it never knew the answer came back.
</details>

**Your task:** The tool result is in a Python variable. The model has not seen it yet. Think about what needs to happen to `messages` and then what to call next to get the model's second response. Both helpers you need are already imported at the top of the file.

**What to observe:** The second model response should request a different tool than the first — it now has new information to act on. If it requests the same tool again, something went wrong with how the result reached the model.

**When this works:** The second response is a JSON string with a different tool name. You have just built the core of an agent.

---

## Mini-Stage 5: Build the Loop

**File:** `student_scaffold/mini_5_simple_loop.py`

**Run:**
```bash
CLIENT=scripted bash launch mini5
```

**Gap this fills:** Mini-Stage 4 shows one round-trip. The real agent needs many. You have the pieces — combine them.

**The concept:** The full agent is the round-trip from mini_4 inside a `for` loop. Instead of manually making a second `runtime.complete()` call, you `continue` after each tool result, and the *loop* calls the model again at the top of the next iteration.

The only new question is: **when do you stop?** The model signals completion by setting `action['final_response']` to a non-empty string.

**Think about it first:** You have a working one-round-trip from mini_4. The scheduling task needs four to five tool calls. What changes if you put the round-trip inside a loop? What does the loop need to know to stop?

<details>
<summary>Answer</summary>

Inside the loop: the `continue` at the end of STEP 3 sends execution back to the top, where the model gets called again with the updated messages. The loop naturally chains round-trips without you manually writing each one. To stop: check `action['final_response']` at the end of each iteration. When it's non-empty, the model is done — store the response and `break`. The `for` loop's upper bound (`runtime.max_model_turns`) is a safety net in case the model never finishes.
</details>

**What is already given:** The loop, STEP 1 (call model), STEP 2 (parse action), STEP 3 (call tool + continue). Everything from mini_1 through mini_4 is already written.

**Your task:** Implement STEP 4 — replace `pass` with the termination logic. When the model has produced a final answer, store it and stop the loop. Look at the action dict to determine when that is.

**What to observe:** When this works, the output should show multiple tool calls (search, open, find slots, create event) followed by a final response. This is the first time you see the full agent working end-to-end.

---

## Mini-Stage 6: Observe Without Guidance

**File:** `student_scaffold/mini_6_observe_prompts.py`

**Run:**
```bash
CLIENT=local bash launch mini6
```

**This file is already complete.** Do not edit it — just run it and read the output.

**What it does:** Runs the full agent loop (same as mini_5) but builds the system prompt with *only* the benchmark's default rules — no `EXTRA_RULES` from `prompts.py`. It prints verbose turn-by-turn output so you can see exactly what the model decides to do without any custom guidance.

**Why this matters:** Before you write rules for `prompts.py`, you need to know what you're fixing. This mini-stage shows you the model's baseline behavior.

**What to observe:**
- Does the model open the note or thread before scheduling, or does it guess at the meeting details?
- Does it call `calendar.find_free_slots`, or does it pick a start time directly?
- Does it pick a start time that conflicts with an existing calendar event?
- Does it invent attendees or meeting titles from memory?

**Note:** This mini-stage requires `CLIENT=local` (the real model). If you have not set up the model connection yet, run `bash launch doctor` first and follow the setup instructions.

**Think about it:** After running, write down one or two specific behaviors you'd want to change. Those observations become your `EXTRA_RULES` in the next step.

---

## Debugging Stage 1

Use these when your score is not what you expect.

**`suite_score` is 0 or blank:** The agent is probably crashing before `runtime.finish()` is reached. Run `bash launch run alex` and look for a Python traceback. Common causes: `parse_action()` raising on malformed JSON (add the try/except from Phase A), a required tool argument missing, or the loop never hitting `final_response`.

**`artifact_read_rate` is 0:** The agent created the event but skipped opening the note or email first. Check your prompt rules — the model needs guidance to open the referenced source before calling `calendar.find_free_slots`. Also check the verbose turn-by-turn output to see what tool sequence the model actually used.

**Agent loops without terminating:** The model never returns a non-empty `final_response`. Check your termination condition — it should test `action.get('final_response', '').strip()`, not just `action.get('final_response')`. Also verify your loop safety limit (`runtime.max_model_turns`) is being checked.

**Wrong title, attendees, or date in the event:** The model is using the user message text instead of the source content. Add a prompt rule requiring it to open the note or email thread before calling `calendar.find_free_slots` or `calendar.create_event`.

---

## Final Stage-1 Agent

**File:** `student_scaffold/agent.py`

**Phase A: Get the mechanics working**

```bash
CLIENT=scripted bash launch run alex
```

The skeleton in `agent.py` is the same four-step loop from mini-stages 1–5. Implement all four steps using the same patterns you already built. The step comments label which mini-stage each pattern came from.

The one new concept is in STEP 2: wrap `parse_action()` in `try/except`. If the model returns malformed JSON, `parse_action()` raises — without a handler, the whole session crashes. On exception: increment `invalid_response_count`, append `{"role": "user", "content": invalid_json_feedback()}` to messages, and `continue`. This tells the model it produced bad output and gives it a chance to retry. (`invalid_json_feedback` is already imported at the top of the file.)

Verify the loop works end-to-end with `CLIENT=scripted` before moving to the real model.

**Phase B: Design your prompt rules**

Once the mechanics work, switch to the real model and start with minimal rules:

```bash
CLIENT=local bash launch run alex
```

If you ran mini_6, you already have observations. If not, comment out your `EXTRA_RULES` in `prompts.py` and run to see the baseline behavior. Then write rules to fix what you observe.

Design tension to keep in mind:
- **Too vague** (e.g., "be helpful"): the model ignores ambiguous guidance and guesses.
- **Too specific** (e.g., "always use note_id 101"): passes visible tests but fails on hidden inputs with different values.
- **Wrong order** (e.g., "create the event, then find free slots"): the model follows the rule even when it's wrong.

The goal is the minimum set of rules that produces reliable behavior on inputs you have not seen. Run `bash launch eval` to score your rules against the visible benchmark.

**Other design choices:**
- **Termination:** Should you trust `final_response` unconditionally, or verify the event was actually created?
- **Error recovery:** How many invalid JSON retries is reasonable? What happens if the model loops without making progress?

Do not hard-code note titles, dates, attendees, or expected tool sequences. Hidden test sessions use different values.

---

## Stage-1 Checkpoint

Complete this before moving to Stage 2.

**Prompt experiment log** — run `bash launch eval` with three different `EXTRA_RULES` configurations and fill in the table:

| Configuration | Strategy (one phrase) | suite_score | artifact_read_rate |
|--------------|----------------------|-------------|-------------------|
| Variant A | | | |
| Variant B | | | |
| Variant C | | | |

Which variant had the most impact, and why?

→

**Termination edge case** — describe a specific scenario where `final_response` is non-empty but the calendar event was not created correctly:

→

**Generalization check** — do any of your prompt rules contain specific note titles, user names, or dates?
- [ ] Yes — remove them before submitting
- [ ] No — good to move on

---

## Ready for Stage 2?

Run `bash launch eval` and confirm `suite_score` is at a level you are happy with. Then move to `student_scaffold_stage2/ARCHITECTURE.md` to start Stage 2.

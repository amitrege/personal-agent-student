# Stage-1 Mini-Stages

Don't start with `agent.py`. Work through these mini-stages first. Each one adds a single concept, and by mini-stage 5 you'll have built every piece of the agent in isolation. `agent.py` is those same pieces assembled into a loop — once you've done the mini-stages, it should feel like connecting things you already understand.

**Run mini-stage 0 first (no reading needed yet):**

```bash
CLIENT=scripted bash launch mini0
```

It prints the available tools and the full system prompt. Spend a few minutes reading the output — the tool names and JSON format you see there are what you'll be working with throughout. Then come back and read these three sections of `ARCHITECTURE.md` before starting mini-stage 1 (about 5 minutes):

- **"What an Agent Is"** — the loop your code implements: ask the model → run a tool → repeat. Every mini-stage builds one piece of this.
- **"The Three Main Objects"** — `runtime`, `session`, and `response`. Know what `runtime.complete()`, `runtime.call_tool()`, and `runtime.finish()` do before writing any code.
- **"What the Model Actually Returns"** — the model always replies with `{"tool_call": ..., "final_response": ...}`. Your code branches on these two fields throughout.

Use `CLIENT=scripted` through mini-stage 5. The scripted client returns deterministic responses so you can learn the code path without waiting for a real model or spending API credits. Switch to the real model for mini-stage 6 and the final agent.

---

## Mini-Stage 0: See the Whole System First

**File:** `student_scaffold/mini_0_finish.py`

You already ran this above. It prints three things:
1. The user message (`session.user_message`) — what the user is asking for
2. Every tool your agent can call, with their parameter names
3. The full system prompt — the instructions the model receives before it sees the user's request

**Look for:** seven tool names (two note tools, two email tools, three calendar tools), and the JSON format block at the end of the system prompt.

Given the user message, which tool would you call first? What argument would you pass? The model makes this decision, but understanding its reasoning is how you write better prompt rules later.

<details>
<summary>Answer</summary>

The user message references a note ("Use my SimpleNote note titled 'Monday planning brief'..."), so the first tool is `simple_note.search_notes` with `query="Monday planning brief"`. That returns a list of matching notes. The model then needs the note's ID to call `simple_note.show_note` and read the full content. Your job in the agent is to execute whatever tool the model requests — you don't decide the sequence, you just run it reliably.
</details>

---

## Mini-Stage 1: Make the First Model Call

**File:** `student_scaffold/mini_1_model_call.py`

**Run:**
```bash
CLIENT=scripted bash launch mini1
```

Mini-stage 0 returns a hardcoded string — it never actually asks the model anything. Here you fix that: send the user's request to the model and get back a real response.

The call is `runtime.complete(messages, require_json=True)`. It sends the conversation history to the model and returns a response object. You pass the system prompt as the first message, then the user message, then any tool results that have accumulated so far. `require_json=True` constrains the model to reply with valid JSON — without it, parsing becomes unreliable.

You have the user message and the system prompt. What does the model need before it can suggest a first action?

<details>
<summary>Answer</summary>

Both. The system prompt tells the model what tools exist and what format to use. The user message tells it what to do. Without the system prompt the model doesn't know it should respond with JSON or that it has any tools. Without the user message it has nothing to act on. Check the `runtime.complete()` signature in ARCHITECTURE.md under "The Three Main Objects" for how to pass them.
</details>

**Your task:** Replace `response = ...` with a call to `runtime.complete`. The signature is in `ARCHITECTURE.md` under "The Three Main Objects". All arguments are keyword-only.

**Working when** the output ends with a JSON string containing `tool_call` and `final_response` keys. If you see a Python exception, reread the call signature — keyword-only means you must write `messages=...`, not pass positional arguments.

---

## Mini-Stage 2: Parse the Model's Response

**File:** `student_scaffold/mini_2_parse_action.py`

**Run:**
```bash
CLIENT=scripted bash launch mini2
```

The model returned a JSON string. A string can't be subscripted like a dict — you can't write `response.content["tool_call"]`. Before you can branch on the model's decision, you need to turn that string into a Python object.

`parse_action(content)` does this. It calls `json.loads()` under the hood, handles edge cases, and returns a plain dict with exactly two fields:
- `action["tool_call"]` — a dict `{"name": ..., "arguments": {...}}` if the model wants a tool run; `None` otherwise
- `action["final_response"]` — a non-empty string when the model is done; `""` otherwise

Every turn in the agent loop branches on exactly these two fields. This mini-stage is about getting comfortable with that dict.

`response.content` is the string `'{"tool_call": {"name": "simple_note.search_notes", ...}, "final_response": ""}'`. What needs to happen before you can write `if action.get("tool_call")`?

<details>
<summary>Answer</summary>

Parse it. `parse_action()` is that parsing step. It turns the raw string into a Python dict you can branch on. The function also normalizes some edge cases (aliases, missing fields) so you don't have to worry about them in your loop logic.
</details>

**Your task:** Replace `action = ...`. `parse_action` is already imported at the top of the file. Look at what you have (the response object from mini-stage 1) and what the function expects as input.

Print `action` and look inside `action["tool_call"]` — you'll need those field names in the next mini-stage.

**Working when** printing `action` gives you a dict. If you get a `TypeError` or `None`, check what you're passing to `parse_action`.

---

## Mini-Stage 3: Execute One Tool

**File:** `student_scaffold/mini_3_one_tool.py`

**Run:**
```bash
CLIENT=scripted bash launch mini3
```

You know which tool the model wants to call — but the model can't run it. The model produces text; it has no ability to reach into a file system, database, or calendar API. Your Python code does that on its behalf.

`runtime.call_tool(tool_name, arguments, turn_index)` runs the named tool in the benchmark world and returns three values: the tool name used, the arguments it was called with, and the result. The result contains real benchmark data — a list of notes, a note's full content, a set of available time slots, a calendar confirmation.

You have `action["tool_call"]["name"]` and `action["tool_call"]["arguments"]`. What needs to happen before the model can use this information?

<details>
<summary>Answer</summary>

Your code runs the tool and captures the result. The model lives inside `runtime.complete()` — it produces a string saying "call this tool with these arguments." It has no other capabilities. Only your Python code can actually execute a tool and retrieve data. Once you have the result, you need to put it back into the conversation so the model can see it and plan its next step. That's mini-stage 4.
</details>

**Your task:** Replace the sentinel with a call to `runtime.call_tool`. Pull the tool name and arguments from the action dict and pass them through. Full signature in `ARCHITECTURE.md`.

Print `result` to see what the benchmark returns.

**Working when** `result` contains actual benchmark data, not `None`. If you get `KeyError` or `TypeError`, reread how `call_tool` expects its arguments.

---

## Mini-Stage 4: Complete the Round Trip

**File:** `student_scaffold/mini_4_one_round_trip.py`

**Run:**
```bash
CLIENT=scripted bash launch mini4
```

You ran the tool and got the result. The model still doesn't know — `result` is just a Python variable sitting outside the conversation. The model can only see what's in `messages`.

Closing the loop takes two steps: add the tool result to `messages` using `tool_result_message(tool_name, result)`, then call `runtime.complete()` again with the updated list. The model sees the full exchange — original request, its first response, the tool result — and returns a new response deciding what to do next.

That's one complete round trip: model asks → tool runs → model sees result. The full agent is many of these chained together.

After the tool runs, how does the model find out what it returned?

<details>
<summary>Answer</summary>

You add the result to `messages` using `tool_result_message()`, which formats it as a user-role message the model can read. Then you call `runtime.complete()` again with the updated list. If you skip the append step, the model never sees the result — it will request the same tool again on the next call, because from its perspective nothing happened after its first response.
</details>

**Your task:** append the tool result to `messages`, then call `runtime.complete()` again to get the second response. Both helpers (`tool_result_message` and `assistant_message`) are already imported.

**Working when** the second model response requests a *different* tool than the first. It now has new information and is choosing what to do next.

---

## Mini-Stage 5: Build the Loop

**File:** `student_scaffold/mini_5_simple_loop.py`

**Run:**
```bash
CLIENT=scripted bash launch mini5
```

Mini-stage 4 showed one round trip. A real scheduling task needs four or five — search the note, open it, find free slots, create the event. The pattern is the same each time; you just need to repeat it without writing each iteration by hand.

The structure is already in place: the `for` loop, the model call (STEP 1), the parse (STEP 2), the tool call and result append (STEP 3). The one missing piece is STEP 4: knowing when to stop.

The model signals completion by setting `action["final_response"]` to a non-empty string. When that happens, store the response and `break`. The `for` loop's upper bound (`runtime.max_model_turns`) is a safety net — if the model never signals done, the loop terminates cleanly instead of running forever.

After `continue` at the end of STEP 3, execution returns to the top of the loop and the model gets called again with the updated `messages`. The loop naturally chains round trips without you writing each one manually.

**Your task:** Implement STEP 4 — replace `pass` with the termination logic. Check `action["final_response"]`, store it, and `break`.

**Working when** the output shows a sequence of tool calls (search, open, find slots, create event) followed by a natural-language final response. You've just built a working agent from scratch.

---

## Mini-Stage 6: Watch Without Guidance

**File:** `student_scaffold/mini_6_observe_prompts.py`

**Run:**
```bash
CLIENT=local bash launch mini6
```

Run it without editing. It runs the same loop as mini-stage 5, but with only the benchmark's default rules in the system prompt — no `EXTRA_RULES` from `prompts.py`.

Watch for the model's baseline behavior before you add any guidance. Does it open the note before scheduling? Does it call `find_free_slots`, or does it pick a time directly? Does it invent attendees? The behaviors you want to fix here become the rules you write in `prompts.py`.

This requires `CLIENT=local` (the real model). If you haven't set up the model connection yet, run `bash launch doctor` first.

Write down one or two specific behaviors you'd change — not "it was wrong" but "it called `create_event` without calling `find_free_slots` first." That specificity is what makes a useful rule.

---

## When Things Go Wrong

**`suite_score` is 0 or blank:** the agent is crashing before `runtime.finish()` is reached. Run `bash launch run alex` and look for a Python traceback. Common causes: `parse_action()` raising on malformed JSON (the `try/except` in STEP 2 of `agent.py` handles this), a required tool argument missing, or the loop ending without hitting `final_response`.

**`artifact_read_rate` is 0:** the agent created the event but never opened the note or email first. The model jumped straight from the user message to scheduling. Add a prompt rule requiring it to read the source before calling `find_free_slots` or `create_event`, and check the verbose turn-by-turn output to see exactly what sequence was used.

**Agent loops without terminating:** the model never returns a non-empty `final_response`. Check your termination condition — test `action.get("final_response", "").strip()`, not just `action.get("final_response")` (an empty string is falsy but a whitespace-only string is not). Also verify the loop's turn limit is being checked.

**Wrong title, attendees, or date:** the model used the user message text instead of the source content. It needs a rule telling it to open the note or email thread before calling `find_free_slots` or `create_event`.

---

## The Final Agent

**File:** `student_scaffold/agent.py`

**Phase A: Get the mechanics working**

```bash
CLIENT=scripted bash launch run alex
```

The skeleton in `agent.py` is the same four-step loop from mini-stages 1–5, assembled in order. The step comments tell you which mini-stage each pattern came from. Implement all four steps.

One piece is new compared to the mini-stages: STEP 2 wraps `parse_action()` in a `try/except`. With a real model, malformed JSON happens occasionally. Without a handler, the whole session crashes on the first bad response. The handler increments `invalid_response_count`, appends `{"role": "user", "content": invalid_json_feedback()}` to messages (so the model knows it produced bad output and can retry), and `continue`s. (`invalid_json_feedback` is already imported.)

Verify the loop works end-to-end with `CLIENT=scripted` before switching to the real model.

**Phase B: Design your prompt rules**

```bash
CLIENT=local bash launch run alex
```

If you ran mini-stage 6, you already have observations. If not, comment out `EXTRA_RULES` in `prompts.py` and run once to see the baseline.

Three failure modes to watch for:
- **Too vague** ("be helpful") — the model ignores guidance that isn't specific enough.
- **Too specific** ("always use note_id 101") — passes visible tests but fails on hidden inputs with different values.
- **Wrong order** ("create the event, then find free slots") — the model follows the rule even when it leads it astray.

The goal is the minimum set of rules that produces reliable behavior on inputs you haven't seen. Run `bash launch eval` to score against the visible benchmark.

Two more design decisions to work through:
- **Termination:** trust `final_response` unconditionally, or verify the event was actually created?
- **Error recovery:** how many invalid-JSON retries before giving up?

Don't hard-code note titles, dates, attendees, or expected tool sequences. Hidden test sessions use different values.

---

## Stage-1 Checkpoint

Run `bash launch eval` with three different `EXTRA_RULES` configurations and fill in the table.

**Prompt experiment log:**

| Configuration | Strategy (one phrase) | suite_score | artifact_read_rate |
|--------------|----------------------|-------------|-------------------|
| Variant A | | | |
| Variant B | | | |
| Variant C | | | |

Which variant had the most impact, and why?

→

**Termination edge case** — describe a specific scenario where `final_response` is non-empty but the calendar event wasn't created correctly:

→

**Generalization check** — do any of your rules contain specific note titles, user names, or dates?
- [ ] Yes — remove them before submitting
- [ ] No — good to move on

---

## Ready for Stage 2?

Confirm `suite_score` is at a level you're happy with, then open `student_scaffold_stage2/ARCHITECTURE.md` to start Stage 2.

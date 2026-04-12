# Stage-2 Mini-Stages

Do not start by editing `agent.py`. Work through these mini-stages first. Each one adds one memory concept. By Mini-Stage 4 you will have seen every building block the full Stage-2 agent uses — then `agent.py` is those blocks assembled, with two design choices to make.

**Before you start — read these three sections of `ARCHITECTURE.md` first (≈5 min total):**
- **"You Can Already Schedule a Meeting" and "What the Problem Is"** — explains why Stage 1 fails when the same user returns across sessions. Read this to understand the gap memory fills before you start filling it.
- **"The Memory API"** — shows the exact signatures for `runtime.write_memory()` and `runtime.search_memory()`. Know what `key`, `value`, `evidence`, and `confidence` mean before mini-stage 1.
- **"Why Python, Not Prompt Rules"** — explains why you intercept `calendar.create_event` arguments in Python rather than adding a rule to the system prompt. This is the key design decision in Stage 2 and the answer comes up in the Stage-2 checkpoint.

Use `CLIENT=scripted` for all mini-stages. The memory system works the same way with the scripted client as with the real model.

---

## Mini-Stage 0: Observe Memory

**File:** `student_scaffold_stage2/mini_0_observe_memory.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini0
```

**This file is already complete.** Do not edit it — just run it and read the output.

**What it does:** Prints three things before returning:
1. The user message for the current session
2. The current memory mode (controls whether writes and reads are active)
3. The result of searching memory before anything has been written

**What to observe:**
- Memory starts empty at the beginning of every user's session history. The search returns `[]`.
- Note the `memory_mode`. In development it will be `full`, meaning writes and reads both work.
- Look at the user message. Does this session contain a time preference? If so, what should the stored value be?

**When this works:** You will see the user message, `memory_mode=full`, and `[]` for the memory search. Last line: `Memory exploration complete.`

**Think about:** The benchmark runs sessions for each user in order — session `s1`, then `s2`, then `s3`. If memory is empty at the start of `s1`, what has to happen in `s1` for `s2` to find something?

<details>
<summary>Answer</summary>

Session `s1` must write a memory. If `s1` never calls `runtime.write_memory(...)`, then when `s2` calls `runtime.search_memory(...)`, the list will still be empty — even if the user mentioned a preference in `s1`. The write is what makes it persist. That is the gap mini_1 fills.
</details>

---

## Mini-Stage 1: Write One Memory

**File:** `student_scaffold_stage2/mini_1_write_memory.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini1
```

**Gap this fills:** Stage 1 forgot everything after a session ended. Now you need to store a preference when the user states one, so a later session can find it.

**The concept:** `runtime.write_memory(...)` stores a small fact about the current user that persists across sessions. The helper `extract_direct_time_preference(text)` in `common.py` already handles the detection — it returns `"morning"`, `"afternoon"`, or `None`. Your job is to call `write_memory` when the result is not `None`.

**Think about it first:** `extract_direct_time_preference` can return `None`. What should happen when it does?

<details>
<summary>Answer</summary>

When the function returns `None`, the user did not state a preference in this message. You should not write anything to memory — writing `None` or `""` as a preference value would corrupt the stored data. The file already handles this: when the result is `None`, it returns early with "No new time preference in this session." You only need to fill in the write case.
</details>

**Your task:** Replace `memory = ...` with a call to `runtime.write_memory`. The signature is in `ARCHITECTURE.md` under "The Memory API". Decide what `key`, `value`, `evidence`, and `confidence` should be — the key you choose here must match what you use in mini-stages 2 and 3.

**What to observe:** Run against both users. The session with a stated preference should print a stored memory dict. The session without one should print the early-return message.

**When this works:** Sessions with a preference print a stored memory entry. Sessions without one exit early. If you see `NotImplementedError`, the sentinel is still in place.

---

## Mini-Stage 2: Read Memory Across Sessions

**File:** `student_scaffold_stage2/mini_2_read_memory.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini2
```

**Gap this fills:** Writing memory is not enough. The later session has to retrieve it. This mini-stage confirms that a memory written in session `s1` is visible in session `s2`.

**The concept:** The benchmark runs all sessions for a user in order. Memory written during `s1` is available when `s2` starts. `runtime.search_memory(key="preferred_time_window")` returns the full list of memories written for this user with that key — including everything from earlier sessions.

**Think about it first:** `search_memory` returns a list, not a single value. Why might there be more than one entry?

<details>
<summary>Answer</summary>

A user might state a preference in session 1 and then a different preference in session 3. Each call to `write_memory` appends a new entry — it does not overwrite the old one. The list grows over time. That is why `latest_time_window(memories)` reads the list in reverse: the most recent preference is the one that should be used. You will use `latest_time_window` starting in mini_3.
</details>

**Your task:** Replace `memories = ...` with a call to `runtime.search_memory`. Use the same key you used in mini-stage 1.

**What to observe:** Run against both users. The key session to watch is the one that does *not* contain a time preference. No write happens in that session, but the memory from the earlier session should still be retrievable:

```
s1 memories: [{'key': 'preferred_time_window', 'value': 'afternoon', ...}]
s2 memories: [{'key': 'preferred_time_window', 'value': 'afternoon', ...}]
```

Session `s2` found the memory even though it did not write anything this session. That is the whole point.

**When this works:** A session that did not write a preference still finds the one written by an earlier session. If the list is always `[]`, check that you passed `key="preferred_time_window"` as a keyword argument.

---

## Mini-Stage 3: Choose a Slot From Memory

**File:** `student_scaffold_stage2/mini_3_choose_slot.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini3
```

**Gap this fills:** Memory should change what the agent does, not just sit in a list. This mini-stage isolates the slot-choice decision.

**The concept:** `choose_preferred_slot(available_slots, preference)` returns the earliest slot for `"morning"`, the latest for `"afternoon"`, and `None` if there is no preference. It never invents a slot — it only picks from the list you pass in.

**Think about it first:** What should happen if the user's preferred slot is not available?

<details>
<summary>Answer</summary>

`choose_preferred_slot` returns the earliest or latest slot from whatever list you pass. If the only available slot is 09:00 and the user prefers afternoons, the function returns 09:00 — it cannot return a slot that is not in the list. Memory constrains the *choice*, not the *result*. If `choose_preferred_slot` returns `None` (no preference or no slots), your code leaves the model's choice unchanged. This is the safe behavior: memory as a preference, not a hard override.
</details>

**Your task:** Replace `chosen_slot = ...`. The `choose_preferred_slot` function is already imported — pass the slots and the preference. Both are already defined above the TODO.

**What to observe:**
```
preference=afternoon; available_slots=['09:00', '16:00']; chosen_slot=16:00
preference=morning;   available_slots=['09:00', '16:00']; chosen_slot=09:00
preference=None;      available_slots=['09:00', '16:00']; chosen_slot=None
```

**When this works:** The chosen slot matches the preference when one exists, and is `None` when there is no preference. If you see `NotImplementedError`, the `chosen_slot = ...` sentinel is still in place.

---

## Mini-Stage 4: Add Memory to the Tool Loop

**File:** `student_scaffold_stage2/mini_4_memory_loop.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini4
```

**Gap this fills:** Mini-stages 1–3 showed each memory concept in isolation. This mini-stage puts slot choice inside the real Stage-1 tool loop.

**The concept:** The loop in this file is the Stage-1 loop, almost unchanged. The memory write and search already happen before the loop. The one new moment is inside the loop: when the model requests `calendar.create_event`, your code intercepts the arguments, uses `choose_preferred_slot` to pick from the free slots found earlier in this session, and overrides `arguments["start_time"]` if a preference is known.

**Think about it first:** Why intercept at `calendar.create_event` instead of just adding a rule to the system prompt that says "pick an afternoon slot"?

<details>
<summary>Answer</summary>

Two reasons. First, the model is stochastic — it might follow the rule, or it might not. Code is deterministic: if your Python sets `arguments["start_time"] = preferred_slot`, the event is always created with that time. Second, you need the slot to be one the calendar confirmed as free. The `last_available_slots` variable is populated when `calendar.find_free_slots` returns — so by the time `create_event` is called, you know exactly which slots were available this session. Choosing from that list guarantees you never book a slot that is already taken.

The system prompt rule is still useful as a hint to the model (it is already added in `memory_rules`), but the Python interception is the enforcement.
</details>

**Your task:** In the `calendar.create_event` block, replace `preferred_slot = ...`. You already used `choose_preferred_slot` in mini-stage 3 — the same call applies here. After replacing the sentinel, the next two lines in the file handle the case where a preferred slot was found.

**What to observe:** The agent still runs the full scheduling loop — opens the note or thread, finds free slots, creates the event. The difference is that it picks the user's preferred valid slot. If the user prefers afternoons and the free slots were `["09:00", "16:00"]`, the event should be created at `16:00`.

**When this works:** With `CLIENT=scripted`, the run completes with a final response confirming the scheduled meeting, and the start time reflects the memory preference. If you see `NotImplementedError`, the `preferred_slot = ...` sentinel is still in place.

---

## Debugging Stage 2

Use these when your Stage 2 score is not what you expect.

**`preference_accuracy` is low:** The agent is not picking the preferred slot when multiple slots are available. Check three things: (1) Does `extract_direct_time_preference` return the right value for the user message? Print it before the loop. (2) Is `runtime.search_memory` returning the stored preference in session 2? Print `memories` before the loop. (3) Is `choose_preferred_slot` being called and its return value used to override `arguments["start_time"]`?

**`memory_accuracy` is low:** Memory was not written when it should have been, or was not read correctly. Run `CLIENT=scripted bash launch stage2-mini2` to verify that memory written in session 1 is visible in session 2 for your key. If the list is always empty, check that your `write_memory` and `search_memory` calls use the same key string.

**Agent picks wrong slot even with memory:** Confirm `choose_preferred_slot` receives the slots list from *this session's* `find_free_slots` call — not an empty list or a stale one. Add a print statement before the `create_event` interception to see what `last_available_slots` contains at that moment.

**Stage-1 scores regressed:** Your Stage-2 `agent.py` might have a bug introduced when adding the memory pieces. Test with `CLIENT=scripted bash launch stage2-eval` to isolate from model variance, then compare turn-by-turn output to your working Stage-1 agent.

---

## Final Stage-2 Agent

**File:** `student_scaffold_stage2/agent.py`

**Phase A: Get the mechanics working**

```bash
STUDENT_AGENT_MODULE=student_scaffold_stage2.agent SCENARIO=memory_stage_v1 CLIENT=scripted bash launch run alex
```

`agent.py` has a class skeleton and a docstring describing the three additions. Your job:

1. Copy your Stage-1 `run_session` implementation into `student_scaffold_stage2/agent.py` as the starting point.
2. Add the three memory pieces described in the docstring, using the patterns from the mini-stages:
   - Before the loop: write memory if a preference is detected (mini_1)
   - Before the loop: search memory for any stored preference (mini_2)
   - Inside the loop, at `calendar.create_event`: pick the preferred valid slot (mini_3 + mini_4)
3. Make any design decisions you want around error handling, the system prompt memory rule, and edge cases.

Verify end-to-end with `CLIENT=scripted` before switching to the real model.

**Phase B: Run against the memory scenario**

```bash
CLIENT=scripted bash launch stage2-eval
```

Then switch to the real model for a full evaluation:

```bash
CLIENT=local bash launch stage2-eval
```

**Required design choices (everyone makes these):**

- **When to write memory.** `extract_direct_time_preference` only triggers on direct words like "afternoon" or "morning". A user who says "I'm usually free in the second half of the day" will return `None`. For Stage 2, this is intentional — Stage 3 will replace the rule with a classifier. But you can extend the rule in Stage 2 if you want more coverage. Just document what you changed and why.

- **What if the user changes their mind?** `latest_time_window` trusts the most recent write. Think about whether that is always right for your use case — and look at the Design Extensions in ARCHITECTURE.md for alternatives.

- **System prompt rule wording.** When `active_preference` is set, you have a memory rule to add. The exact phrasing affects how reliably the model follows it. Try different versions and observe the difference.

**Optional extensions (go further if you want):**

These are not required and do not affect your Stage 2 benchmark score, but they are worth exploring if Stage 2 feels straightforward:

- **Second preference dimension.** The memory system supports any key. Add `"preferred_duration"` (short/long) or another preference type. Extend `choose_preferred_slot` to account for both dimensions when selecting a slot.

- **Stability-based conflict resolution.** Replace `latest_time_window` with a function that only acts on a preference if it appears in at least two sessions (or accumulates above a confidence threshold). When does this perform better? When does it perform worse?

- **Implicit preference capture.** After `calendar.find_free_slots` returns and the model selects a slot (without any stated preference), write a low-confidence memory entry recording which time window was chosen. Over multiple sessions, does this implicit signal converge toward the user's actual preference?

These ideas matter later. The social arena extra credit rewards agents that handle messier memory behavior, such as temporary preferences, corrections, and confidence-based conflict resolution.

Do not hard-code users, note titles, dates, attendees, or expected slots. Hidden sessions use different values.

---

## Stage-2 Checkpoint

Fill in this table and the two blanks before submitting.

**Memory design summary:**

| Aspect | Your implementation |
|--------|-------------------|
| Condition for writing memory | |
| Conflict resolution strategy | |
| System prompt rule text (when preference is active) | |

**Signal gap** — name one type of preference signal the current design misses (hint: think about where preferences might appear other than the opening message):

→

**Conflict scenario** — describe a case where `latest_time_window` (trust most recent) leads to the wrong slot being picked:

→

---

## Ready for Stage 3?

Run the Stage 2 benchmark and confirm your scores. Then move to `student_scaffold_stage3/ARCHITECTURE.md` to start Stage 3.

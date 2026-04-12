# Stage-2 Mini-Stages

Don't start with `agent.py`. Work through these mini-stages first. Each one isolates one piece of the memory system, and by the end of mini-stage 4 you'll have seen every new concept in action. `agent.py` is then just those pieces added to your Stage-1 loop.

**Run mini-stage 0 first (no reading needed yet):**

```bash
CLIENT=scripted bash launch stage2-mini0
```

It shows the current memory mode and the result of a memory search before anything has been written. Then come back and read these three sections of `ARCHITECTURE.md` before starting mini-stage 1 (about 5 minutes):

- **"You Can Already Schedule a Meeting" and "What the Problem Is"** — the concrete scenario that motivates memory. Read this before writing anything so you understand what gap you're filling.
- **"The Memory API"** — the exact signatures for `runtime.write_memory()` and `runtime.search_memory()`. Know what `key`, `value`, `evidence`, and `confidence` mean before mini-stage 1.
- **"The One Rule About Memory"** and **"Where Memory Fits In The Loop"** — why you intercept `calendar.create_event` arguments in Python code rather than adding a system prompt rule. This is the central design decision in Stage 2.

Use `CLIENT=scripted` for all mini-stages. The memory system works identically with the scripted client and the real model.

---

## Mini-Stage 0: See What Memory Looks Like

**File:** `student_scaffold_stage2/mini_0_observe_memory.py`

You already ran this above. It shows three things:
1. The user message for the current session
2. The current memory mode (controls whether writes and reads are active)
3. The result of searching memory before anything has been written

Memory starts empty — the search returns `[]`. For session `s2` to find a preference, session `s1` must have written one first. The next three mini-stages build that write-then-read chain.

**Look for:** `memory_mode=full` (writes and reads both work) and `[]` from the memory search.

**Think about:** the benchmark runs each user's sessions in order — `s1`, then `s2`. If session `s1` never calls `runtime.write_memory(...)`, what will session `s2` find when it searches?

<details>
<summary>Answer</summary>

An empty list. Memory doesn't persist automatically — your code has to write it explicitly. If `s1` finishes without writing anything, `s2` will get `[]` from `runtime.search_memory(...)` even if the user mentioned a preference in `s1`. The write is what makes it persist across sessions.
</details>

---

## Mini-Stage 1: Write a Memory

**File:** `student_scaffold_stage2/mini_1_write_memory.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini1
```

A preference the user states in session 1 is only useful if a later session can retrieve it. Your job is to store it when it's stated.

The detection is already handled for you: `extract_direct_time_preference(text)` in `common.py` looks for direct phrases like "afternoon" or "morning" and returns one of three values — `"morning"`, `"afternoon"`, or `None`. Your job is to call `runtime.write_memory(...)` when the result is not `None`.

`extract_direct_time_preference` returns `None` when the user doesn't state a preference. What should happen then?

<details>
<summary>Answer</summary>

Nothing — don't write. Writing `None` or `""` as a preference value would corrupt the stored data and confuse any session that reads it later. Only write when you have something real to store. The file already handles the `None` case with an early return; you just need to fill in the write path.
</details>

**Your task:** Replace `memory = ...` with a call to `runtime.write_memory`. The signature is in `ARCHITECTURE.md` under "The Memory API". The key you choose here is important — it must match exactly what you use in mini-stages 2 and 3.

Run against both users. The session with a stated preference should print a stored memory dict. The session without one should exit early.

**Working when** sessions with a preference print a stored memory entry, and sessions without one exit early with no write. If you see `NotImplementedError`, the sentinel is still in place.

---

## Mini-Stage 2: Read Memory Across Sessions

**File:** `student_scaffold_stage2/mini_2_read_memory.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini2
```

Writing memory is only useful if you can confirm that what was written in one session is visible in the next.

`runtime.search_memory(key="preferred_time_window")` returns a list of all memories ever written for this user with that key, ordered oldest first. The benchmark runs sessions in order, so anything written during `s1` is available when `s2` runs.

`search_memory` returns a list, not a single value. Why might there be more than one entry?

<details>
<summary>Answer</summary>

A user might state a preference in session 1 and then a different one in session 3. Each `write_memory` call appends a new entry — it doesn't overwrite. The list grows over time. That's why `latest_time_window(memories)` in `common.py` reads the list in reverse: the most recent preference is the one that should win. You'll use that helper starting in mini-stage 3.
</details>

**Your task:** Replace `memories = ...` with a call to `runtime.search_memory`. Use the same key you chose in mini-stage 1.

The key session to watch is the one that *doesn't* contain a time preference. No write happens in that session — but you should still see the memory from the earlier one:

```
s1 memories: [{'key': 'preferred_time_window', 'value': 'afternoon', ...}]
s2 memories: [{'key': 'preferred_time_window', 'value': 'afternoon', ...}]
```

**Working when** the session that didn't write a preference still finds the one written earlier. If the list is always `[]`, check that you passed `key="preferred_time_window"` as a keyword argument.

---

## Mini-Stage 3: Choose a Slot From Memory

**File:** `student_scaffold_stage2/mini_3_choose_slot.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini3
```

A stored preference is only useful if it changes which slot gets booked. This mini-stage connects the memory read to the slot selection.

`choose_preferred_slot(available_slots, preference)` handles this: it returns the earliest available slot for `"morning"`, the latest for `"afternoon"`, and `None` if there's no preference. It never invents a slot — it only selects from the list you pass in.

What should happen when the user's preferred time window has no available slots?

<details>
<summary>Answer</summary>

`choose_preferred_slot` returns the best available slot from whatever list you give it. If the only open slot is `09:00` and the user prefers afternoons, it returns `09:00` — it can't return a slot that isn't available. Memory is a preference, not a hard constraint. If `choose_preferred_slot` returns `None` (no preference, or no slots), you leave the model's original choice in place. This is the safe behavior: when in doubt, don't override.
</details>

**Your task:** Replace `chosen_slot = ...`. `choose_preferred_slot` is already imported — pass the slots and the preference. Both are defined above the TODO.

**Working when** the output shows:
```
preference=afternoon; available_slots=['09:00', '16:00']; chosen_slot=16:00
preference=morning;   available_slots=['09:00', '16:00']; chosen_slot=09:00
preference=None;      available_slots=['09:00', '16:00']; chosen_slot=None
```

---

## Mini-Stage 4: Add Memory to the Tool Loop

**File:** `student_scaffold_stage2/mini_4_memory_loop.py`

**Run:**
```bash
CLIENT=scripted bash launch stage2-mini4
```

Mini-stages 1–3 each isolated one piece of the memory system. This one puts them together inside the actual Stage-1 tool loop.

The loop is your Stage-1 loop almost unchanged. The memory write and search happen before the loop. The one new moment is inside the loop: when the model requests `calendar.create_event`, your code intercepts the call, uses `choose_preferred_slot` to select from the free slots found earlier in this session, and overrides `arguments["start_time"]` if a preference is known.

Why intercept `create_event` arguments in Python rather than adding a system prompt rule like "pick an afternoon slot"?

<details>
<summary>Answer</summary>

Two reasons. First, the model is stochastic — it might follow the rule, or it might not, depending on how the conversation unfolds. Python code is deterministic: if your code sets `arguments["start_time"] = preferred_slot`, the event is always created with that time. Second, the preferred slot must come from the list `calendar.find_free_slots` returned *for this session* — those are the slots confirmed free on this specific day. Your Python code has that list. The model doesn't; it would have to re-reason about which slots are still available. Intercepting in Python means you never accidentally book a time that wasn't confirmed free.

The system prompt rule is still useful as a hint to the model (the file adds one in `memory_rules`), but the Python interception is the enforcement.
</details>

**Your task:** In the `calendar.create_event` block, replace `preferred_slot = ...` with a call to `choose_preferred_slot`. Same call you used in mini-stage 3 — the slots list and the preference are already available where the TODO sits.

**Working when** the run completes with a final response confirming the scheduled meeting, and the start time reflects the memory preference. If the user prefers afternoons and the free slots were `["09:00", "16:00"]`, the event should be created at `16:00`.

---

## When Things Go Wrong

**`preference_accuracy` is low:** the agent isn't picking the preferred slot when multiple slots are available. Check three things in order: (1) does `extract_direct_time_preference` return the right label for the user message? Print it before the loop. (2) Is `runtime.search_memory` returning the stored preference in session 2? Print `memories` before the loop. (3) Is `choose_preferred_slot` being called and its result used to override `arguments["start_time"]`?

**`memory_accuracy` is low:** memory wasn't written when it should have been, or wasn't read correctly. Run `CLIENT=scripted bash launch stage2-mini2` to confirm that memory written in session 1 is visible in session 2. If the list is always empty, check that your `write_memory` and `search_memory` calls use the same key string.

**Agent picks the wrong slot even with memory:** confirm `choose_preferred_slot` is receiving the slots from *this session's* `find_free_slots` call — not an empty list or a stale one from a previous run. Print `last_available_slots` just before the `create_event` interception to see what it contains.

**Stage-1 scores dropped:** a bug was introduced when adding the memory pieces. Test with `CLIENT=scripted bash launch stage2-eval` to isolate from model variance, then compare turn-by-turn output to your working Stage-1 agent.

---

## The Final Agent

**File:** `student_scaffold_stage2/agent.py`

**Phase A: Get the mechanics working**

```bash
CLIENT=scripted STUDENT_AGENT_MODULE=student_scaffold_stage2.agent SCENARIO=memory_stage_v1 bash launch run alex
```

The `agent.py` docstring describes the three additions to make. Start by copying your Stage-1 `run_session` into this file, then add the memory pieces using the patterns from the mini-stages:
1. Before the loop: write memory if a preference is detected (mini-stage 1)
2. Before the loop: search memory for any stored preference (mini-stage 2)
3. Inside the loop, at `calendar.create_event`: save the slots from `find_free_slots`, then pick the preferred one when `create_event` is requested (mini-stages 3 + 4)

Verify end-to-end with `CLIENT=scripted` before switching to the real model.

**Phase B: Run against the memory scenario**

```bash
CLIENT=scripted bash launch stage2-eval
```

The Stage 2 grade is `min(suite_score, 100 * preference_accuracy, 100 * memory_accuracy)`. All three must be non-zero — a zero on any one collapses the Stage 2 score to zero regardless of the others.

Then with the real model:

```bash
CLIENT=local bash launch stage2-eval
```

**Design choices to work through:**

- **When to write memory.** `extract_direct_time_preference` only catches direct phrases like "afternoon" or "morning". A user who says "I'm usually free in the second half of the day" returns `None`. Stage 3 replaces this keyword rule with a classifier. You can extend it in Stage 2 if you want — document what you changed and why.

- **What if the user changes their mind?** `latest_time_window` trusts the most recent write. Is that always right? The Design Extensions in `ARCHITECTURE.md` discuss alternatives.

- **System prompt rule wording.** When `active_preference` is set, add a hint to the system prompt. The exact phrasing affects how reliably the model follows it — try a few versions. Note that `prompts.py` in this stage already contains a set of pre-filled scheduling rules that are always active; your memory hint adds to those at runtime.

**Optional extensions (not required, don't affect Stage 2 score):**

These are worth exploring if Stage 2 feels straightforward, and they're useful preparation for the social arena:

- **A second preference dimension.** Add `"preferred_duration"` or another key. How would you update `choose_preferred_slot` to account for both when selecting a slot?
- **Stability-based conflict resolution.** Replace `latest_time_window` with a function that only acts on a preference if it appears in at least two sessions. When does this perform better? When does it perform worse?
- **Implicit preference signals.** When a user picks a slot without stating a preference, write a low-confidence memory recording which time window was chosen. Over multiple sessions, does this pattern converge toward their actual preference?

Don't hard-code users, note titles, dates, attendees, or expected slots. Hidden sessions use different values.

---

## Stage-2 Checkpoint

Fill in this table and the two blanks before submitting.

**Memory design summary:**

| Aspect | Your implementation |
|--------|-------------------|
| Condition for writing memory | |
| Conflict resolution strategy | |
| System prompt rule text (when preference is active) | |

**Signal gap** — name one type of preference signal the current design misses (hint: think about where preferences might appear besides the opening user message):

→

**Conflict scenario** — describe a case where `latest_time_window` (trust most recent) leads to the wrong slot being picked:

→

---

## Ready for Stage 3?

Run the Stage 2 benchmark and confirm your scores, then open `student_scaffold_stage3/ARCHITECTURE.md` to start Stage 3.

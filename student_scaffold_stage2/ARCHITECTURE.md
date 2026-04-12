# Stage-2 Architecture

---

## What You Will Learn in Stage 2

By the end of Stage 2 you will understand:
- How to add **persistent memory** to a stateless agent so preferences survive across sessions
- Why **deterministic Python code** is used to enforce constraints that a stochastic model cannot reliably enforce alone
- How a working AI system often combines three kinds of components: a model that reasons, classical code that enforces hard constraints, and a learned component that improves with data (Stage 3 adds the third)
- The design tradeoffs in memory schemas: what to store, when to write, and how to resolve conflicts

---

## How to Use This Document

You do not need to read this end-to-end before writing code.

**Before mini-stage 0:** Read "You Can Already Schedule a Meeting" and "What the Problem Is" and "The Memory API" (~5 min).

**While working through mini-stages 1–4:** Use the relevant section as a reference — the call signatures and memory object shape are all here.

**Before agent.py:** Read "Where Memory Fits In The Loop" and "The One Rule About Memory".

Everything else is reference — skip it and come back when you need it.

---

## The Architecture of This System

Before looking at the Stage-2 problem, it is worth naming the structure of the system you are building across all three stages:

```text
┌─────────────────────────────────────────────────────────┐
│  Language model  — reasons, decides which tools to call │
├─────────────────────────────────────────────────────────┤
│  Deterministic Python code — enforces hard constraints  │
│    • tool loop, message history, JSON parsing           │
│    • memory write/read, slot selection (Stage 2)        │
├─────────────────────────────────────────────────────────┤
│  Learned component — improves with data  (Stage 3)      │
│    • trained preference classifier                      │
└─────────────────────────────────────────────────────────┘
```

Stage 1 built the first layer. Stage 2 builds the second layer's memory system. Stage 3 replaces a hand-written rule in the second layer with a trained classifier from the third layer.

The key design principle of Stage 2 is that **deterministic code, not prompt rules, enforces the scheduling constraint**. You will see why as you work through the memory interceptor. It is the most important design idea in this stage.

---

## You Can Already Schedule a Meeting

In Stage 1 you built an agent that reads a user's request, opens a note or email, extracts the meeting details, and creates a calendar event. It works correctly every time — for a single session.

Stage 2 starts from the same agent. The tool loop, the JSON parsing, the system prompt — all of it carries over. The only question is what happens when the same user comes back for a second session.

---

## What the Problem Is

Alex sends this request in session 1:

```text
Use my SimpleNote note 'Sync with design team' to schedule the meeting.
I prefer afternoon slots — my mornings are usually packed.
```

Your Stage-1 agent extracts the meeting details, finds a free slot, and creates the event. But it never stores the fact that Alex prefers afternoons. The session ends and that information is gone.

Three days later, Alex is back:

```text
Use my Gmail thread 'Q3 kickoff' to schedule the meeting.
```

Your Stage-1 agent has no memory of the afternoon preference. It asks the model to pick a slot, and the model picks 9:00am. Alex gets a morning meeting she didn't want.

This is not a bug in Stage 1 — it was designed to be stateless. Stage 2 adds the missing piece: a way to store a useful fact about a user and retrieve it in a later session.

---

## What a Personalized Agent Does

The agent loop from Stage 1 stays the same. Stage 2 adds two moments outside that loop:

```text
1. Read the user message
2. If the user states a time preference, write it to memory          ← new
3. Search memory for a stored preference                             ← new
4. Run the Stage-1 tool loop (search source → open source → find slots → create event)
5. Before creating the event, use memory to choose among free slots  ← new (inside the loop)
```

Steps 2 and 3 happen before the model is ever called. Step 5 happens at one specific moment inside the loop: when the model requests `calendar.create_event`. Your code intercepts that call, checks memory, and overrides only the `start_time` argument if a preference is known.

The model still does everything else: decides which tools to call, extracts the meeting title, date, duration, and attendees, chooses which note or email thread to open.

---

## What a Memory Object Looks Like

`runtime.search_memory(key="preferred_time_window")` returns a list of dicts. Each entry is one memory written by a previous call to `runtime.write_memory(...)`. A typical list after one write looks like this:

```python
[
    {
        "key": "preferred_time_window",
        "value": "afternoon",
        "evidence": "I prefer afternoon slots — my mornings are usually packed.",
        "confidence": 1.0,
    }
]
```

If no preference has ever been written for this user, the list is empty:

```python
[]
```

If the user expressed a preference in session 1, then expressed a different preference in session 3, the list has two entries. `latest_time_window(memories)` (already in `common.py`) picks the most recent valid one by reading the list in reverse.

---

## The Memory API

Stage 2 adds two runtime calls.

**Write a memory:**

```python
runtime.write_memory(
    key="preferred_time_window",
    value="afternoon",   # or "morning"
    evidence=session.user_message,
    confidence=1.0,
)
```

`key` is the name of the fact. `value` is the fact itself. `evidence` is the raw text that justified the write — useful for debugging. `confidence` is how certain you are (1.0 means a direct statement; lower values are used by the Stage-3 learned component).

**Read memories:**

```python
memories = runtime.search_memory(key="preferred_time_window")
```

Returns a list of all memories ever written for this user with that key, ordered oldest first. An empty list means no preference has been stored.

**Key and value design:** The key is a string you choose. A natural choice for time-of-day preference is:

```text
key:   "preferred_time_window"
value: "morning" or "afternoon"
```

You can use different names as long as your `write_memory` and `search_memory` calls use the same key. The memory system supports any key/value pair — `"preferred_duration"`, `"preferred_day"`, or anything else you want to store. (The benchmark grader checks for `preferred_time_window` specifically, so keep that key for the required implementation. Extensions can use additional keys.)

---

## The One Rule About Memory

Memory should only choose among valid options. It should never override the calendar.

If `calendar.find_free_slots` returns `["09:00", "16:00"]` and memory says the user prefers afternoons, pick `16:00`. If `calendar.find_free_slots` returns only `["09:00"]` — because `16:00` is already booked — then pick `09:00`. Memory is a preference, not a hard constraint.

The helper `choose_preferred_slot(available_slots, preference)` in `common.py` handles this correctly. It returns the earliest available slot for `"morning"`, the latest for `"afternoon"`, and `None` if there is no preference or no slots.

```python
choose_preferred_slot(["09:00", "16:00"], "afternoon")  # → "16:00"
choose_preferred_slot(["09:00", "16:00"], "morning")    # → "09:00"
choose_preferred_slot(["09:00", "16:00"], None)         # → None  (no preference)
choose_preferred_slot([], "afternoon")                  # → None  (no slots)
```

When `choose_preferred_slot` returns `None`, leave the model's chosen `start_time` unchanged.

**Design note: why intercept in Python rather than adding a prompt rule?**

You could instead add a system prompt rule like: `"If the user prefers afternoons, always pick the latest available slot."` This is simpler to write, but less reliable. The model is stochastic — it might follow the rule, or it might not, depending on how the rest of the conversation unfolds. A Python interception is deterministic: once `arguments["start_time"]` is set in your code, the event is always created with that time, regardless of what the model chose.

There is a second reason. The slot must come from the list `calendar.find_free_slots` returned for this session. Your Python code already has that list. The model does not — it would have to re-reason about which slots are available. By intercepting in Python, you guarantee you never pass a slot that was not confirmed free.

This is one specific design. It has its own tradeoffs. You will examine them in the Stage-2 Reflection.

---

## Where Memory Fits In The Loop

Two helpers in `common.py` handle the preference detection:

```python
extract_direct_time_preference(text) -> str | None
```

Looks for direct phrases like "afternoon", "morning", "earlier", "late in the day". Returns `"morning"`, `"afternoon"`, or `None`.

```python
latest_time_window(memories) -> str | None
```

Reads the list returned by `search_memory` and returns the most recent valid preference, or `None` if there is none.

**Design note: why trust the most recent write?**

The memories list is ordered oldest-first. `latest_time_window` reads it in reverse and returns the first valid value it finds. This assumes the user's most recent stated preference is the most accurate one — a reasonable default.

It is not the only possible policy. You might instead trust the highest-confidence write, or require two consistent writes before acting on a preference. Each choice is a tradeoff between stability (acting on sparse signals) and responsiveness (updating quickly when preferences change). You will examine this in the Stage-2 Reflection.

**Where to add things in your agent:**

At a high level, the Stage-2 agent is your Stage-1 agent with three additions:

- **Before the tool loop:** detect a preference in the user message; if found, write it to memory. Then search memory for any stored preference for this user.
- **Inside the tool loop:** when the model requests `calendar.create_event`, check whether memory has an active preference. If so, use `choose_preferred_slot` to pick the best available slot and override `start_time`.

One implementation detail to track: `choose_preferred_slot` needs the list of slots that `calendar.find_free_slots` returned *in this session*. You need to capture that list when `find_free_slots` runs so it is available at the `create_event` step.

<details>
<summary>Stuck? Click for a flow-level sketch (try without this first)</summary>

```text
Detect preference in user message → write to memory if found

Search memory → get active_preference

--- Stage-1 tool loop ---
for each turn:
    ask model → parse action
    if tool_call is find_free_slots:
        run it → save the returned slots for later
    if tool_call is create_event:
        if active_preference and saved slots exist:
            pick preferred slot → override start_time argument
        run the tool
    add result to messages
--- end loop ---
```

This sketch omits error handling, JSON retries, and the fallback case where no preference is stored. Those are design choices you make.
</details>

---

## Memory Modes

The benchmark can run your agent in three memory modes:

```text
full          memory writes and reads both work normally
profile_blind writes may happen, but reads return an empty list
no_memory     writes are silently dropped; reads always return an empty list
```

You do not need to implement these modes — the runtime handles them. Write your code using `runtime.write_memory()` and `runtime.search_memory()` normally. The benchmark uses these modes to measure how much your agent benefits from memory.

---

## Design Extensions (Optional)

The required Stage-2 implementation supports one preference type with a fixed conflict resolution strategy. These extensions are not part of the Stage-2 grade, but they are useful preparation for the social arena extra credit, where richer memory and conflict handling can improve the leaderboard score.

**1. Additional preference types.** The memory system supports any key. What if users also express preferences about meeting length ("I like to keep meetings under 30 minutes") or day of week ("I try to keep Fridays light")? You could add a second memory write/read for `"preferred_duration"` or `"preferred_day"` and pass the result to slot selection. How would you update `choose_preferred_slot` to handle both dimensions at once?

**2. Conflict resolution alternatives.** `latest_time_window` always trusts the most recent write. What if instead you only acted on a preference after it appeared in two or more sessions (stability check)? Or weighted entries by confidence (the Stage-3 classifier produces a non-1.0 confidence that could feed into this)? Implement an alternative to `latest_time_window` and compare its behavior on the visible eval. A stronger version of this idea is especially useful in the social arena, where users may give temporary overrides or change their minds.

**3. Implicit preference signals.** The current design only reads `session.user_message`. But preferences might also appear implicitly: if a user picks the afternoon slot every time even without stating a preference, that pattern might be worth capturing. How would you detect and store an implicit preference from the slot-selection history?

---

## Next Step

Open `MILESTONES.md`. It walks you through four mini-stages that build the memory system one concept at a time, then shows you where the pieces fit in the final agent.

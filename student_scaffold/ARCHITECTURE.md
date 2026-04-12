# Stage-1 Architecture

The Stage-1 agent is a loop: the model decides which tool to call, your code runs it and feeds the result back, and this repeats until the task is done. This document explains each component of that loop and the objects your code works with.

If you haven't already, run `CLIENT=scripted bash launch mini0` before reading — it shows the tools and prompt format that this document describes. Then read "What an Agent Is" and "The Three Main Objects" before mini-stage 1. Use the rest as a reference while building.

---

## You Already Know How to Call a Model

In the base model exercise you wrote something like:

```python
response = model.chat(messages=[{"role": "user", "content": "What time should I schedule this meeting?"}])
print(response.content)
```

That works for open-ended questions. But this project asks you to schedule an *actual* meeting: create a real calendar event using the exact details from a note or email thread. Try the naive approach — ask the model "schedule this meeting from my note titled 'Monday planning brief'" — and you'll get a confident-sounding answer that is completely made up. The model has no access to your notes. It has no access to your calendar. It will invent a date, invent attendees, and produce a response that looks plausible but isn't real.

**The model can reason, but it cannot reach into your data systems.** That is the gap an agent fills.

---

## What an Agent Is

An agent is a loop. Instead of calling the model once and returning an answer, your code:

1. Asks the model: "given everything you know so far, what should happen next?"
2. The model says: "call this tool with these arguments"
3. Your code runs the tool and gets the result
4. Your code adds the result to the conversation
5. Go back to step 1 — repeat until the model says it is done

The model acts as the *brain* — it decides which tool to call and what arguments to pass. Your Python code is the *hands* — it actually runs the tools and feeds results back. Neither can complete the task alone.

Changing the tool list changes what the agent can do; the loop stays the same.

```text
while task is not done:
    ask the model: "what should happen next?"
    the model returns an action — either "call this tool" or "here is the final answer"
    if the action is a tool call:
        run the tool
        add the result to the conversation history
    if the action is a final answer:
        stop and return it
```

Everything in this project is an implementation of this loop.

---

## What the Model Actually Returns

The model is instructed to always respond with JSON. A typical first response looks like:

```json
{
  "tool_call": {
    "name": "simple_note.search_notes",
    "arguments": {"query": "Monday planning brief"}
  },
  "final_response": ""
}
```

Your code reads `tool_call`, sees that the model wants to search for a note, calls `runtime.call_tool("simple_note.search_notes", {"query": "Monday planning brief"}, ...)`, gets back a list of matching notes, appends that result to the conversation, and calls the model again. The model then sees the search results and asks for the next tool. This pattern repeats.

When the model is finally done — after opening the note, finding a free slot, and creating the event — it sets `final_response` and leaves `tool_call` empty:

```json
{
  "tool_call": null,
  "final_response": "I've scheduled the Lab planning sync for Tuesday at 9:00am."
}
```

Your code sees `final_response` is non-empty, stops the loop, and returns the answer to the benchmark.

---

## How the Benchmark Calls Your Code

When you run `bash launch mini1` (or `bash launch run`), the benchmark loads your module, finds the `build_agent` function, creates your agent, and calls `run_session(session, runtime)` for each task.

Put all your code inside `run_session`. The `session` and `runtime` arguments are provided by the benchmark — you don't create them. The class structure and `__init__` are boilerplate required by the runner; don't modify them.

```python
class MiniStageAgent(StudentAgent):
    def run_session(self, session, runtime):
        # ← everything you write goes here
        ...
```

`session` is the current task. `runtime` is your interface to the model and tools. Both are covered in "The Three Main Objects" below.

---

## If You Have Used the OpenAI SDK Before

You have probably written something like:

```python
from openai import OpenAI
client = OpenAI()
resp = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
)
print(resp.choices[0].message.content)
```

`runtime.complete()` is the same idea with a simpler interface:

```python
response = runtime.complete(
    messages=[{"role": "user", "content": "Hello"}],
    require_json=True,
)
print(response.content)   # same text, less nesting
```

`response.content` replaces `resp.choices[0].message.content` — less nesting. `require_json=True` constrains the model to reply with JSON so your code can parse it reliably.

**Why not call the OpenAI API directly?** The runtime lets the benchmark swap in different backends without you changing your agent code. It also tracks which events your agent created (needed for grading) and enforces turn limits. In Stage 2, the same `runtime` object provides access to memory — the interface stays consistent across all stages.

---

## The Three Main Objects

### `session` — the current task

The benchmark delivers each task to your code as a `session` object. The only field you need is:

```python
session.user_message
```

For example: `"Use my SimpleNote note titled 'Monday planning brief' to schedule the meeting."`

Everything the agent does starts from this string.

### `runtime` — the interface to everything else

Instead of calling an LLM API directly, you call `runtime`. The benchmark controls which model is used, tracks costs, and enforces turn limits — none of that lives in your agent code. The runtime also provides `CLIENT=scripted` mode, which replaces the real model with a deterministic test client.

The calls you will use in every agent:

```python
# Ask the model what to do next (returns a response object; use response.content for the text)
response = runtime.complete(
    messages=[{"role": "system", "content": system_prompt}] + messages,
    require_json=True,
)

# Run a tool the model requested
tool_name, arguments, result = runtime.call_tool(
    tool_name="simple_note.search_notes",
    arguments={"query": "Monday planning brief"},
    turn_index=turn_index,
)

# Return the final answer to the benchmark
return runtime.finish(final_response)
```

Two more calls you will see in the mini-stages:

```python
runtime.list_tools()             # list of ToolSpec objects, one per available tool
runtime.prompt_rules()           # default instruction rules from the benchmark
runtime.default_final_response() # generate a fallback response from the last tool call
                                 # (used when the loop ends without a model final_response)
```

Note: all arguments to `runtime.complete()` and `runtime.call_tool()` are keyword-only — you must write `messages=...`, `tool_name=...`, etc.

### `messages` — the conversation history

The model has no memory between calls. You maintain it by passing the full history on every call. `messages` is a plain list of dicts that grows as the conversation progresses:

```python
messages = [
    {"role": "user",      "content": "Use my note 'Monday planning brief' to schedule..."},
    {"role": "assistant", "content": "{\"tool_call\": {\"name\": \"simple_note.search_notes\", ...}}"},
    {"role": "user",      "content": "TOOL_RESULT simple_note.search_notes: [{\"id\": \"note-42\", ...}]"},
    # ... next assistant turn, next tool result, ...
]
```

Every call to the model includes the full `messages` list. That's how the model knows what tools have already been called and what results came back.

Two helpers in `common.py` handle the formatting for you:

```python
assistant_message(response)            # wraps a model response into a messages entry
tool_result_message(tool_name, result) # wraps a tool result into a messages entry
```

---

## The System Prompt

Before the conversation starts, the model needs instructions: what tools exist, what format to respond in, and any task-specific guidance. The `build_system_prompt(runtime)` helper in `common.py` assembles this from:

- Default rules from the benchmark (tool descriptions and response format)
- Your custom rules from `prompts.py`

The rules in `prompts.py` are a real design choice. A model given only generic instructions might call tools in the wrong order, skip steps, or use the wrong fields. More specific rules produce more reliable behavior, but rules that are wrong or contradictory break things too. You will work through this tradeoff after the mini-stages.

---

## The Expected Task Flow

A successful scheduling session looks like this:

```text
1. Read session.user_message
2. Decide whether the request points to a note (SimpleNote) or an email thread (Gmail)
3. Search for the referenced source
4. Open the full source
5. Extract: Meeting title, Date, Duration minutes, Attendees
6. Call calendar.find_free_slots with the extracted date and duration_minutes
7. Pick a valid slot from the results
8. Call calendar.create_event with the exact title, date, start_time, duration_minutes, and attendees
9. Return a final response with runtime.finish(...)
```

The model drives steps 2–8 by requesting tool calls. Your code executes them and feeds results back. The grader checks two things: that the calendar event was created with the correct fields, and that you opened the referenced source before scheduling. The wording of the final response does not matter.

Do not hard-code note titles, dates, or attendees. Hidden test sessions use different values.

---

## Next Step

Open `MILESTONES.md`. It walks you through six mini-stages that build toward the full agent one concept at a time.

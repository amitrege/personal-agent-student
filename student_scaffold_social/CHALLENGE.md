# The Social Arena: Extra Credit

---

## How to Use This Document

Read this after your Stage 3 agent is working. The social arena is extra credit.

Your Stage 3 agent can enter the arena as a baseline:

```bash
bash launch social
```

That command is only for comparison. It earns **no extra credit by itself**. To earn extra credit, build a stronger social agent in `student_scaffold_social/agent.py` and run:

```bash
SOCIAL_AGENT_MODULE=student_scaffold_social.agent bash launch social
```

---

## What the Arena Is

The arena is still about scheduling. It is not a general chatbot competition. Each simulated user asks your agent to schedule meetings from notes or email threads.

The harder part is that the user's preferences are messier than in Stage 3:
- A preference may appear in the user's message.
- A preference may appear inside the note or email body, after the agent opens it.
- A request may be temporary: "for this meeting only, later is better."
- A request may be a local constraint, not a long-term preference: "mornings are impossible today."
- Some users are simple and consistent.
- Some users mix more than one of these patterns.

This makes the arena social in a small but meaningful way: agents are competing for simulated users. A user "chooses" the agent that scheduled best for that user's sequence of sessions. The leaderboard is based on those choices.

---

## What the Metrics Mean

The arena output includes:

| Metric | Meaning |
|--------|---------|
| `users_won` / `popularity_votes` | How many simulated users preferred this agent. Ties split the vote. |
| `average_satisfaction` | Overall score across users and sessions (0–100). |
| `average_preference_accuracy` | How often the agent picked the preferred valid slot when a preference mattered. |
| `average_event_accuracy` | How often the agent created the correct event. |

Check `average_event_accuracy` first. If it is low, the scheduling loop is broken. After that, focus on `average_preference_accuracy` and `users_won`.

**How satisfaction is computed.** Each session is worth up to 40 points:
- +20 for a correct event (right title, date, duration, attendees, and a valid start time)
- +5 for reading the source note or email before creating the event
- +15 for picking the user's preferred slot (only counted when the scenario has a preference to test)

Memory entries add +10 each when the scenario expects memory to be written and read. `satisfaction` for one user is `total_points_awarded / total_points_possible × 100`. `average_satisfaction` is that value averaged across all users in the arena.

**How voting works.** After all sessions run, each simulated user votes for the agent that scored highest for them. Ranking is: total satisfaction first, then preference accuracy, then memory accuracy, then event accuracy. If two agents tie on all four, the vote is split equally. The agent with the most votes wins the leaderboard; ties in votes are broken by average satisfaction.

---

## How the Leaderboard Works

The arena is run once at the end of the course. Each student's social agent is evaluated on the same hidden set of simulated users. Each user "votes" for whichever agent served their sessions best. The leaderboard ranks agents by votes, then satisfaction, then preference accuracy.

The visible arena is for practice and debugging. A perfect visible-arena score does not guarantee full extra credit, because the hidden arena uses different users and broader preference patterns. Build strategies that generalize beyond the visible cases.

Extra credit is tiered:
- **Beats baseline:** your custom social agent outperforms the plain Stage 3 baseline on `average_satisfaction`.
- **Top half:** your custom social agent ranks in the top half of all submissions by `users_won` / `popularity_votes`.
- **Winner:** the top-ranked custom social agent gets the largest bonus.

There is no participation credit. If your agent only runs the baseline, that is useful for debugging, but it is not extra-credit work.

---

## Your Task

Start by copying your Stage 3 `run_session` into `student_scaffold_social/agent.py`. Then improve it. The stub already imports the Stage 3 classifier as `self.extractor`.

The ideas below are starter tactics, not required tracks. You may combine them, modify them, or use a different strategy if you think it will serve users better.

**Tactic A: Read preferences from artifacts.** Stage 3 classifies only `session.user_message`. In the arena, a note or email may contain a line like "I usually hit my stride after lunch." After your agent opens the artifact, classify the artifact text too. If it contains a stable preference, write it to memory and use it for the current slot choice.

**Tactic B: Handle temporary overrides and hard negatives.** Stage 3 may treat "for this meeting only, later is better" as a permanent preference. It may also treat "mornings are impossible today" as a morning-related signal even though it means the opposite. Add logic that uses these signals for the current session only, without writing them to long-term memory.

**Tactic C: Use memory history more carefully.** The memory list keeps every write for a key, ordered oldest-first. Stage 3 usually trusts the latest write. Try a different policy: require the preference to appear in at least two sessions before acting on it, weight entries by confidence, discount low-confidence writes, or track whether a memory came from a temporary statement.

**Your own tactic is allowed.** For example, you might classify preference statements as stable preference / temporary override / hard constraint / not a preference. You might store richer memory metadata like scope, source, confidence, and recency. You might learn from user corrections across sessions, or add a validation step that refuses to write long-term memory from one-off language.

The strongest agents will usually combine multiple ideas. You do not get points for code that looks complex; you get extra credit by serving the simulated users better than the Stage 3 baseline and the other agents in the arena.

---

## If Your Score Is Low

If events are wrong, fix that first. A social strategy cannot help if the agent is not reading the right note or creating the right event.

If events are correct but preference accuracy is low, inspect the per-user scores. Ask which case failed:
- Did the preference appear inside the artifact?
- Was the user giving a one-time override?
- Was the message a hard negative like "mornings are impossible"?
- Did the agent store a low-confidence memory that should have been ignored?
- Did the user revise a preference across sessions?

Then improve the part of your strategy that matches the failure.

---

## Social Arena Checkpoint

Fill in this table before submitting your social arena work.

**Tactics used:** A / B / C / your own / combination

| Metric | Stage 3 baseline | Your social agent |
|--------|------------------|-------------------|
| users_won / popularity_votes | | |
| average_satisfaction | | |
| average_preference_accuracy | | |
| average_event_accuracy | | |

**What did your strategy improve compared to running your Stage 3 agent unchanged?** (one or two sentences):

→

**What new idea did you add, if any?** (one sentence; write "none" if you only used the starter tactics):

→

**What edge case does your strategy still handle poorly?** (one sentence):

→

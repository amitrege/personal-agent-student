from __future__ import annotations


# DESIGN SPACE
#
# The rules below are instructions added to the model's system prompt. The model will try
# to follow them, so specific rules produce more reliable behavior. But there are tradeoffs:
#
#   Too few rules  → the model may guess, skip steps, or call tools in the wrong order
#   Too many rules → the prompt gets long; conflicting rules confuse the model
#   Wrong rules    → the model will follow them even if they hurt
#
# Start by running the agent and watching what it does. Then ask:
#
#   1. Does the model know it must open the referenced note or thread *before* scheduling?
#      Without that data, it cannot know the meeting title, date, duration, or attendees.
#
#   2. How should it decide whether the user is referring to a note (SimpleNote) or an
#      email thread (Gmail)? What language in the user message is the signal?
#
#   3. What fields does calendar.create_event require? Where does the model find them?
#      If the model guesses a field value, the event will be wrong.
#
#   4. How specific should your rules be? Rules that name exact tool sequences work well
#      on the visible test cases but may break on hidden ones with different wording.
#      Rules that describe *goals* (not steps) tend to generalize better.
#
# The two rules below are a starting point. You are expected to improve them.

EXTRA_RULES = [
    "Use tools to inspect the referenced note or email thread before scheduling.",
    "Use tool results rather than guessing missing scheduling fields.",
]

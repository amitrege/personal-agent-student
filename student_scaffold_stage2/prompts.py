from __future__ import annotations


EXTRA_RULES = [
    "Figure out whether the user referenced a SimpleNote note or a Gmail thread.",
    "If the user referenced a note, call simple_note.search_notes first and then simple_note.show_note.",
    "If the user referenced a thread, call gmail.show_inbox_threads first and then gmail.show_thread.",
    "After opening the source, extract Meeting title, Date, Duration minutes, and Attendees exactly.",
    "Then call calendar.find_free_slots with the extracted date and duration_minutes.",
    "When memory gives a preferred time window, use it only to choose among valid free slots.",
    "Then call calendar.create_event with the exact title, date, start_time, duration_minutes, and attendees.",
    "When the event is created, return a short final_response confirming the schedule.",
]

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .base import ToolSpec


def _normalize_field(s: str) -> str:
    """Lowercase + collapse whitespace for event field comparison.

    LLMs sometimes reformat text extracted from notes/emails (different
    capitalization, extra spaces).  Normalizing before comparison prevents
    false failures that have nothing to do with the agent's logic.
    """
    return " ".join(s.strip().lower().split())


@dataclass
class Event:
    id: str
    session_id: str
    title: str
    date: str
    start_time: str
    duration_minutes: int
    attendees: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "title": self.title,
            "date": self.date,
            "start_time": self.start_time,
            "duration_minutes": self.duration_minutes,
            "attendees": self.attendees,
        }


@dataclass
class Note:
    note_id: int
    title: str
    body: str
    tags: list[str]
    updated_at: str

    def summary(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "title": self.title,
            "tags": self.tags,
            "updated_at": self.updated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "title": self.title,
            "body": self.body,
            "tags": self.tags,
            "updated_at": self.updated_at,
        }


@dataclass
class EmailMessage:
    sender: str
    recipients: list[str]
    body: str
    sent_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "recipients": self.recipients,
            "body": self.body,
            "sent_at": self.sent_at,
        }


@dataclass
class EmailThread:
    email_thread_id: int
    subject: str
    participants: list[str]
    messages: list[EmailMessage]
    updated_at: str

    def summary(self) -> dict[str, Any]:
        return {
            "email_thread_id": self.email_thread_id,
            "subject": self.subject,
            "participants": self.participants,
            "snippet": "Open this thread with gmail.show_thread to read the scheduling details.",
            "updated_at": self.updated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "email_thread_id": self.email_thread_id,
            "subject": self.subject,
            "participants": self.participants,
            "messages": [message.to_dict() for message in self.messages],
            "updated_at": self.updated_at,
        }


class CampusToolsWorld:
    def __init__(self, scenario: dict[str, Any], user_id: str) -> None:
        self.scenario = scenario
        self.user_id = user_id
        self.user = deepcopy(scenario["users"][user_id])
        self.events: list[Event] = [
            Event(
                id=item["id"],
                session_id=item.get("session_id", "seed"),
                title=item["title"],
                date=item["date"],
                start_time=item["start_time"],
                duration_minutes=item["duration_minutes"],
                attendees=item["attendees"],
            )
            for item in self.user.get("seed_calendar", [])
        ]
        self.notes: list[Note] = [
            Note(
                note_id=int(item["note_id"]),
                title=item["title"],
                body=item["body"],
                tags=list(item.get("tags", [])),
                updated_at=item.get("updated_at", "2026-04-01T09:00:00"),
            )
            for item in self.user.get("seed_notes", [])
        ]
        self.threads: list[EmailThread] = [
            EmailThread(
                email_thread_id=int(item["email_thread_id"]),
                subject=item["subject"],
                participants=list(item.get("participants", [])),
                messages=[
                    EmailMessage(
                        sender=message["sender"],
                        recipients=list(message.get("recipients", [])),
                        body=message["body"],
                        sent_at=message.get("sent_at", "2026-04-01T09:00:00"),
                    )
                    for message in item.get("messages", [])
                ],
                updated_at=item.get("updated_at", "2026-04-01T09:00:00"),
            )
            for item in self.user.get("seed_threads", [])
        ]
        self.memories: list[dict[str, Any]] = [
            dict(item)
            for item in self.user.get("seed_memories", [])
            if isinstance(item, dict)
        ]
        self.active_session: dict[str, Any] | None = None
        self._event_counter = 0
        self._memory_counter = len(self.memories)

    def list_tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="simple_note.search_notes",
                description="Search note titles and note bodies.",
                parameters={
                    "query": {"type": "string", "required": True},
                    "page_limit": {"type": "integer", "required": False},
                },
            ),
            ToolSpec(
                name="simple_note.show_note",
                description="Open one note by note_id.",
                parameters={
                    "note_id": {"type": "integer", "required": True},
                },
            ),
            ToolSpec(
                name="gmail.show_inbox_threads",
                description="Search email thread subjects and recent message text.",
                parameters={
                    "query": {"type": "string", "required": True},
                    "page_limit": {"type": "integer", "required": False},
                },
            ),
            ToolSpec(
                name="gmail.show_thread",
                description="Open one email thread by email_thread_id.",
                parameters={
                    "email_thread_id": {"type": "integer", "required": True},
                },
            ),
            ToolSpec(
                name="calendar.find_free_slots",
                description="Return available start times for the active task date and duration.",
                parameters={
                    "date": {"type": "string", "required": True},
                    "duration_minutes": {"type": "integer", "required": True},
                },
            ),
            ToolSpec(
                name="calendar.create_event",
                description="Create a calendar event for a chosen available slot.",
                parameters={
                    "title": {"type": "string", "required": True},
                    "date": {"type": "string", "required": True},
                    "start_time": {"type": "string", "required": True},
                    "duration_minutes": {"type": "integer", "required": True},
                    "attendees": {"type": "array", "required": True},
                },
            ),
            ToolSpec(
                name="calendar.list_events",
                description="List existing calendar events, optionally for one date.",
                parameters={
                    "date": {"type": "string", "required": False},
                },
            ),
        ]

    def start_session(self, session_id: str) -> None:
        for session in self.user["sessions"]:
            if session["session_id"] == session_id:
                self.active_session = session
                return
        raise KeyError(f"Unknown session_id: {session_id}")

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.active_session is None:
            raise RuntimeError("start_session must be called before any tool use")
        if tool_name == "simple_note.search_notes":
            return self._search_notes(arguments)
        if tool_name == "simple_note.show_note":
            return self._show_note(arguments)
        if tool_name == "gmail.show_inbox_threads":
            return self._show_inbox_threads(arguments)
        if tool_name == "gmail.show_thread":
            return self._show_thread(arguments)
        if tool_name == "calendar.find_free_slots":
            return self._find_free_slots(arguments)
        if tool_name == "calendar.create_event":
            return self._create_event(arguments)
        if tool_name == "calendar.list_events":
            return self._list_events(arguments)
        raise KeyError(f"Unknown tool: {tool_name}")

    def snapshot(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "events": [event.to_dict() for event in self.events],
            "notes": [note.to_dict() for note in self.notes],
            "threads": [thread.to_dict() for thread in self.threads],
            "memories": list(self.memories),
        }

    def write_memory(
        self,
        *,
        key: str,
        value: str,
        evidence: str = "",
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        normalized_key = str(key).strip()
        normalized_value = str(value).strip()
        if not normalized_key or not normalized_value:
            return {
                "stored": False,
                "reason": "empty_key_or_value",
                "key": normalized_key,
                "value": normalized_value,
            }
        self._memory_counter += 1
        item = {
            "id": f"{self.user_id}-m{self._memory_counter}",
            "user_id": self.user_id,
            "session_id": self.active_session["session_id"] if self.active_session else "",
            "key": normalized_key,
            "value": normalized_value,
            "evidence": str(evidence).strip(),
            "confidence": float(confidence),
        }
        self.memories.append(item)
        return item

    def search_memory(self, *, key: str | None = None, query: str = "") -> list[dict[str, Any]]:
        normalized_key = str(key).strip() if key else ""
        normalized_query = str(query).strip().lower()
        results: list[dict[str, Any]] = []
        for memory in self.memories:
            if normalized_key and memory.get("key") != normalized_key:
                continue
            searchable = " ".join(
                str(memory.get(field, ""))
                for field in ("key", "value", "evidence")
            ).lower()
            if normalized_query and normalized_query not in searchable:
                continue
            results.append(dict(memory))
        return results

    def prompt_rules(self) -> list[str]:
        return [
            "You are a campus scheduling assistant working on one independent task at a time.",
            "Before creating an event, inspect the referenced note or email thread.",
            "Use the exact fields from the note or thread when creating the event.",
            "After reading the source, call calendar.find_free_slots with the task date and duration.",
            "Choose the earliest available slot unless the task leaves only one valid option.",
            "Reply with JSON only.",
            "Return either one tool_call or one final_response in each reply.",
        ]

    def close(self) -> None:
        return None

    def evaluate_run(self, session_runs: list[Any]) -> dict[str, Any]:
        run_map = {run.session_id: run for run in session_runs}
        scores: dict[str, Any] = {
            "correct_sessions": 0,
            "read_sessions": 0,
            "preference_sessions": 0,
            "preference_correct_sessions": 0,
            "sessions": {},
        }
        session_count = max(len(self.user["sessions"]), 1)
        awarded = 0
        possible = 0
        for session in self.user["sessions"]:
            run = run_map.get(session["session_id"])
            created_events = [self._event_by_id(event_id) for event_id in (run.created_event_ids if run else [])]
            created_events = [event for event in created_events if event is not None]
            event = created_events[-1] if created_events else None
            expected = session["expected"]["event"]
            preferred_start = expected.get("preferred_start")
            task = session["task"]
            correct = bool(
                event
                and _normalize_field(event.title) == _normalize_field(task["title"])
                and event.date == task["date"]
                and event.duration_minutes == int(task["duration_minutes"])
                and sorted(_normalize_field(a) for a in event.attendees)
                == sorted(_normalize_field(a) for a in task["attendees"])
                and event.start_time in expected["valid_starts"]
            )
            read_artifact = self._read_artifact_before_create(
                tool_calls=run.tool_calls if run else [],
                artifact=session["artifact"],
            )
            if correct:
                scores["correct_sessions"] += 1
            if read_artifact:
                scores["read_sessions"] += 1
            session_score = (20 if correct else 0) + (5 if read_artifact else 0)
            session_possible = 25
            preferred_correct = None
            if preferred_start:
                preferred_correct = bool(correct and event and event.start_time == preferred_start)
                scores["preference_sessions"] += 1
                session_possible += 15
                if preferred_correct:
                    scores["preference_correct_sessions"] += 1
                    session_score += 15
            scores["sessions"][session["session_id"]] = {
                "correct_event": correct,
                "read_artifact": read_artifact,
                "preferred_start": preferred_start,
                "preferred_start_correct": preferred_correct,
                "selected_start": event.start_time if event else None,
                "score": session_score,
            }
            awarded += session_score
            possible += session_possible
        memory_score = self._evaluate_expected_memories()
        if memory_score["expected_count"]:
            awarded += memory_score["correct_count"] * 10
            possible += memory_score["expected_count"] * 10
            scores["memory"] = memory_score
        scores["event_accuracy"] = round(scores["correct_sessions"] / session_count, 2)
        scores["artifact_read_rate"] = round(scores["read_sessions"] / session_count, 2)
        if scores["preference_sessions"]:
            scores["preference_accuracy"] = round(
                scores["preference_correct_sessions"] / scores["preference_sessions"],
                2,
            )
        if memory_score["expected_count"]:
            scores["memory_accuracy"] = round(
                memory_score["correct_count"] / memory_score["expected_count"],
                2,
            )
        scores["total"] = round(awarded / max(possible, 1) * 100, 2)
        return scores

    def _search_notes(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip().lower()
        page_limit = _coerce_int(arguments.get("page_limit"), default=5)
        if not query:
            return {"notes": []}
        matches = [
            note.summary()
            for note in self.notes
            if query in note.title.lower() or query in note.body.lower()
        ]
        return {"notes": matches[:page_limit]}

    def _show_note(self, arguments: dict[str, Any]) -> dict[str, Any]:
        note_id = _coerce_int(arguments.get("note_id"))
        if note_id is None:
            return {"error": "simple_note.show_note requires note_id"}
        for note in self.notes:
            if note.note_id == note_id:
                return note.to_dict()
        return {"error": f"Unknown note_id: {note_id}"}

    def _show_inbox_threads(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip().lower()
        page_limit = _coerce_int(arguments.get("page_limit"), default=5)
        if not query:
            return {"threads": []}
        matches = []
        for thread in self.threads:
            latest_body = thread.messages[-1].body.lower() if thread.messages else ""
            if query in thread.subject.lower() or query in latest_body:
                matches.append(thread.summary())
        return {"threads": matches[:page_limit]}

    def _show_thread(self, arguments: dict[str, Any]) -> dict[str, Any]:
        thread_id = _coerce_int(arguments.get("email_thread_id"))
        if thread_id is None:
            return {"error": "gmail.show_thread requires email_thread_id"}
        for thread in self.threads:
            if thread.email_thread_id == thread_id:
                return thread.to_dict()
        return {"error": f"Unknown email_thread_id: {thread_id}"}

    def _find_free_slots(self, arguments: dict[str, Any]) -> dict[str, Any]:
        task = self.active_session["task"]
        date = str(arguments.get("date", "")).strip()
        duration_minutes = _coerce_int(arguments.get("duration_minutes"))
        if not date or duration_minutes is None:
            return {"error": "calendar.find_free_slots requires date and duration_minutes"}
        if date != task["date"] or duration_minutes != int(task["duration_minutes"]):
            return {"error": "Requested date or duration does not match the active session task"}
        unavailable = {event.start_time for event in self.events if event.date == date}
        available_slots = [slot for slot in task["candidate_starts"] if slot not in unavailable]
        return {
            "date": date,
            "duration_minutes": duration_minutes,
            "available_slots": available_slots,
        }

    def _create_event(self, arguments: dict[str, Any]) -> dict[str, Any]:
        task = self.active_session["task"]
        title = str(arguments.get("title", "")).strip()
        date = str(arguments.get("date", "")).strip()
        start_time = str(arguments.get("start_time", "")).strip()
        duration_minutes = _coerce_int(arguments.get("duration_minutes"))
        attendees = _string_list(arguments.get("attendees"))
        if not title or not date or not start_time or duration_minutes is None or not attendees:
            return {
                "error": (
                    "calendar.create_event requires title, date, start_time, "
                    "duration_minutes, and attendees"
                )
            }
        if date != task["date"] or duration_minutes != int(task["duration_minutes"]):
            return {"error": "Requested date or duration does not match the active session task"}
        if start_time not in task["candidate_starts"]:
            return {"error": f"Slot {start_time} is not one of the candidate starts for this task"}
        if any(event.date == date and event.start_time == start_time for event in self.events):
            return {"error": f"Slot {start_time} is not available"}
        self._event_counter += 1
        event = Event(
            id=f"{self.user_id}-e{self._event_counter}",
            session_id=self.active_session["session_id"],
            title=title,
            date=date,
            start_time=start_time,
            duration_minutes=duration_minutes,
            attendees=attendees,
        )
        self.events.append(event)
        return event.to_dict()

    def _list_events(self, arguments: dict[str, Any]) -> dict[str, Any]:
        date = str(arguments.get("date", "")).strip()
        items = [event.to_dict() for event in self.events if not date or event.date == date]
        return {"events": items}

    def _event_by_id(self, event_id: str) -> Event | None:
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def _read_artifact_before_create(
        self,
        *,
        tool_calls: list[dict[str, Any]],
        artifact: dict[str, Any],
    ) -> bool:
        show_tool = "simple_note.show_note" if artifact.get("kind") == "note" else "gmail.show_thread"
        seen_show = False
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            if tool_name == show_tool:
                seen_show = True
            if tool_name == "calendar.create_event":
                return seen_show
        return False

    def _evaluate_expected_memories(self) -> dict[str, Any]:
        expected = [
            item
            for item in self.user.get("expected_memories", [])
            if isinstance(item, dict)
        ]
        results: list[dict[str, Any]] = []
        correct_count = 0
        for item in expected:
            key = str(item.get("key", "")).strip()
            value = str(item.get("value", "")).strip()
            matched = any(
                memory.get("key") == key and str(memory.get("value", "")).strip() == value
                for memory in self.memories
            )
            if matched:
                correct_count += 1
            results.append({"key": key, "value": value, "matched": matched})
        return {
            "expected_count": len(expected),
            "correct_count": correct_count,
            "results": results,
            "stored": list(self.memories),
        }


def _coerce_int(value: Any, *, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []

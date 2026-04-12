from __future__ import annotations

import json
import re
from typing import Any

from .types import ModelResponse


def _extract_tool_result(messages: list[dict[str, Any]], tool_name: str) -> Any | None:
    prefix = f"TOOL_RESULT {tool_name}: "
    for message in reversed(messages):
        content = str(message.get("content", ""))
        if content.startswith(prefix):
            return json.loads(content[len(prefix) :])
    return None


def _latest_user_request(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = str(message.get("content", ""))
        if not content.startswith("TOOL_RESULT "):
            return content
    return ""


def _extract_quoted_phrase(text: str) -> str | None:
    matches = re.findall(r"'([^']+)'|\"([^\"]+)\"", text)
    for left, right in matches:
        choice = left or right
        if choice.strip():
            return choice.strip()
    return None


def _looks_like_note_request(normalized_request: str) -> bool:
    return "simplenote" in normalized_request or " note " in f" {normalized_request} "


def _response(action: dict[str, Any], model_name: str) -> ModelResponse:
    return ModelResponse(
        content=json.dumps(action),
        reasoning_details=None,
        raw_response={},
        model=model_name,
    )


def _parse_duration_minutes(value: str) -> int:
    match = re.search(r"\d+", value)
    if match is None:
        raise ValueError(f"Could not parse duration minutes from: {value!r}")
    return int(match.group(0))


def _field(fields: dict[str, str], aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        if alias in fields:
            return fields[alias]
    raise KeyError(f"Missing task field. Expected one of: {', '.join(aliases)}")


def _parse_task_payload(body: str) -> dict[str, Any]:
    fields: dict[str, str] = {}
    for line in body.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized_key = " ".join(key.strip().lower().split())
        fields[normalized_key] = value.strip()
    attendees_value = _field(fields, ("attendees", "participants", "people"))
    attendees = [item.strip() for item in re.split(r"[,;]", attendees_value) if item.strip()]
    return {
        "title": _field(fields, ("meeting title", "event title", "title")),
        "date": _field(fields, ("date", "meeting date")),
        "duration_minutes": _parse_duration_minutes(
            _field(fields, ("duration minutes", "duration", "length minutes", "length"))
        ),
        "attendees": attendees,
    }


def _first_slot(available_slots: list[str]) -> str:
    if not available_slots:
        raise RuntimeError("No available slots found in scripted client.")
    return sorted(available_slots)[0]


class ScriptedToolUseClient:
    MODEL_NAME = "scripted-stage1"

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        require_json: bool,
        temperature: float = 0.0,
    ) -> ModelResponse:
        del temperature
        if not require_json:
            return ModelResponse(
                content="READY.",
                reasoning_details=None,
                raw_response={},
                model=self.MODEL_NAME,
            )
        user_request = _latest_user_request(messages)
        normalized_request = user_request.lower()
        source_title = _extract_quoted_phrase(user_request) or user_request

        if _looks_like_note_request(normalized_request):
            note_search = _extract_tool_result(messages, "simple_note.search_notes")
            if note_search is None:
                return _response(
                    {
                        "tool_call": {
                            "name": "simple_note.search_notes",
                            "arguments": {"query": source_title, "page_limit": 5},
                        },
                        "final_response": "",
                        "final_explanation": "Need the referenced note before scheduling.",
                    },
                    self.MODEL_NAME,
                )
            note = _extract_tool_result(messages, "simple_note.show_note")
            if note is None:
                note_summaries = note_search.get("notes", []) if isinstance(note_search, dict) else []
                note_id = note_summaries[0]["note_id"]
                return _response(
                    {
                        "tool_call": {
                            "name": "simple_note.show_note",
                            "arguments": {"note_id": note_id},
                        },
                        "final_response": "",
                        "final_explanation": "Need the full note contents before scheduling.",
                    },
                    self.MODEL_NAME,
                )
            task_payload = _parse_task_payload(str(note.get("body", "")))
        else:
            thread_search = _extract_tool_result(messages, "gmail.show_inbox_threads")
            if thread_search is None:
                return _response(
                    {
                        "tool_call": {
                            "name": "gmail.show_inbox_threads",
                            "arguments": {"query": source_title, "page_limit": 5},
                        },
                        "final_response": "",
                        "final_explanation": "Need the referenced email thread before scheduling.",
                    },
                    self.MODEL_NAME,
                )
            thread = _extract_tool_result(messages, "gmail.show_thread")
            if thread is None:
                thread_summaries = thread_search.get("threads", []) if isinstance(thread_search, dict) else []
                thread_id = thread_summaries[0]["email_thread_id"]
                return _response(
                    {
                        "tool_call": {
                            "name": "gmail.show_thread",
                            "arguments": {"email_thread_id": thread_id},
                        },
                        "final_response": "",
                        "final_explanation": "Need the full thread contents before scheduling.",
                    },
                    self.MODEL_NAME,
                )
            latest_body = ""
            messages_list = thread.get("messages", []) if isinstance(thread, dict) else []
            if isinstance(messages_list, list) and messages_list:
                latest_body = str(messages_list[-1].get("body", ""))
            task_payload = _parse_task_payload(latest_body)

        free_slots = _extract_tool_result(messages, "calendar.find_free_slots")
        if free_slots is None:
            return _response(
                {
                    "tool_call": {
                        "name": "calendar.find_free_slots",
                        "arguments": {
                            "date": task_payload["date"],
                            "duration_minutes": task_payload["duration_minutes"],
                        },
                    },
                    "final_response": "",
                    "final_explanation": "Need the free slots before creating the event.",
                },
                self.MODEL_NAME,
            )

        created = _extract_tool_result(messages, "calendar.create_event")
        if created is None:
            available_slots = free_slots.get("available_slots", []) if isinstance(free_slots, dict) else []
            return _response(
                {
                    "tool_call": {
                        "name": "calendar.create_event",
                        "arguments": {
                            "title": task_payload["title"],
                            "date": task_payload["date"],
                            "start_time": _first_slot(available_slots),
                            "duration_minutes": task_payload["duration_minutes"],
                            "attendees": task_payload["attendees"],
                        },
                    },
                    "final_response": "",
                    "final_explanation": "Creating the event in the earliest available slot.",
                },
                self.MODEL_NAME,
            )

        return _response(
            {
                "tool_call": None,
                "final_response": (
                    f"Scheduled '{created['title']}' on {created['date']} at {created['start_time']}."
                ),
                "final_explanation": "The task is complete.",
            },
            self.MODEL_NAME,
        )

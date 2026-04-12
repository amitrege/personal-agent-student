from __future__ import annotations

from dataclasses import dataclass
import importlib
import sys
from typing import Any, Protocol

from .config import Settings
from .json_tools import fallback_final_response, resolve_tool_name
from .worlds.base import ToolSpec, WorldAdapter


@dataclass(frozen=True)
class StudentSettings:
    root: str
    max_model_turns: int
    max_tool_calls: int
    max_completion_tokens: int
    compact_local_prompt: bool
    memory_mode: str
    preference_model_path: str


@dataclass(frozen=True)
class StudentSession:
    scenario_id: str
    user_id: str
    session_id: str
    user_message: str


@dataclass(frozen=True)
class SessionResult:
    final_response: str
    tool_calls: list[dict[str, Any]]
    created_event_ids: list[str]
    trace_events: list[dict[str, Any]]


class StudentAgent(Protocol):
    def run_session(self, session: StudentSession, runtime: "StudentRuntime") -> SessionResult: ...


def load_student_agent(settings: Settings) -> StudentAgent:
    if str(settings.root) not in sys.path:
        sys.path.insert(0, str(settings.root))
    module = importlib.import_module(settings.student_agent_module)
    build_agent = getattr(module, "build_agent", None)
    if build_agent is None:
        raise RuntimeError(
            f"Student scaffold module {settings.student_agent_module!r} does not define build_agent(settings)."
        )
    agent = build_agent(
        StudentSettings(
            root=str(settings.root),
            max_model_turns=settings.max_model_turns,
            max_tool_calls=settings.max_tool_calls,
            max_completion_tokens=settings.max_completion_tokens,
            compact_local_prompt=settings.compact_local_prompt,
            memory_mode=settings.memory_mode,
            preference_model_path=settings.preference_model_path,
        )
    )
    if not hasattr(agent, "run_session"):
        raise RuntimeError(
            f"Student scaffold module {settings.student_agent_module!r} returned an object without run_session()."
        )
    return agent


class StudentRuntime:
    def __init__(
        self,
        *,
        scenario: dict[str, Any],
        world: WorldAdapter,
        model_client: Any,
        settings: Settings,
        user_id: str,
        session: dict[str, Any],
    ) -> None:
        self._scenario = scenario
        self._world = world
        self._model_client = model_client
        self._settings = settings
        self._user_id = user_id
        self.session = StudentSession(
            scenario_id=scenario["id"],
            user_id=user_id,
            session_id=session["session_id"],
            user_message=session["user_message"],
        )
        self._trace_events: list[dict[str, Any]] = []
        self._tool_calls: list[dict[str, Any]] = []
        self._created_event_ids: list[str] = []

    @property
    def max_model_turns(self) -> int:
        return self._settings.max_model_turns

    @property
    def max_tool_calls(self) -> int:
        return self._settings.max_tool_calls

    @property
    def compact_local_prompt(self) -> bool:
        return self._settings.compact_local_prompt

    @property
    def memory_mode(self) -> str:
        return self._settings.memory_mode

    def list_tools(self) -> list[ToolSpec]:
        return self._world.list_tools()

    def prompt_rules(self) -> list[str]:
        return self._world.prompt_rules()

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        require_json: bool = True,
        temperature: float = 0.0,
    ) -> Any:
        return self._model_client.complete(
            messages=messages,
            require_json=require_json,
            temperature=temperature,
        )

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {"type": event_type, "session_id": self.session.session_id}
        event.update(payload)
        self._trace_events.append(event)

    def write_memory(
        self,
        *,
        key: str,
        value: str,
        evidence: str = "",
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        if self._settings.memory_mode == "no_memory":
            payload = {
                "stored": False,
                "reason": "memory_mode=no_memory",
                "key": key,
                "value": value,
            }
            self.record_event("memory_write_skipped", payload)
            return payload
        write_memory = getattr(self._world, "write_memory", None)
        if write_memory is None:
            payload = {
                "stored": False,
                "reason": "world_has_no_memory",
                "key": key,
                "value": value,
            }
            self.record_event("memory_write_skipped", payload)
            return payload
        item = write_memory(
            key=key,
            value=value,
            evidence=evidence,
            confidence=confidence,
        )
        self.record_event("memory_write", {"memory": item})
        return item

    def search_memory(self, *, key: str | None = None, query: str = "") -> list[dict[str, Any]]:
        if self._settings.memory_mode in {"no_memory", "profile_blind"}:
            self.record_event(
                "memory_search_hidden",
                {
                    "key": key,
                    "query": query,
                    "memory_mode": self._settings.memory_mode,
                },
            )
            return []
        search_memory = getattr(self._world, "search_memory", None)
        if search_memory is None:
            self.record_event("memory_search_empty", {"key": key, "query": query})
            return []
        results = search_memory(key=key, query=query)
        self.record_event(
            "memory_search",
            {
                "key": key,
                "query": query,
                "result_count": len(results),
            },
        )
        return results

    def call_tool(
        self,
        *,
        tool_name: Any,
        arguments: dict[str, Any],
        turn_index: int | None = None,
    ) -> tuple[str, dict[str, Any], Any]:
        if len(self._tool_calls) >= self._settings.max_tool_calls:
            raise RuntimeError(f"Tool call cap exceeded in session {self.session.session_id}")
        resolved_tool_name = resolve_tool_name(self._world, tool_name)
        result = self._world.call_tool(resolved_tool_name, arguments)
        self._tool_calls.append(
            {
                "name": resolved_tool_name,
                "arguments": arguments,
                "result": result,
            }
        )
        self._trace_events.append(
            {
                "type": "tool_call",
                "session_id": self.session.session_id,
                "turn_index": turn_index,
                "tool_name": resolved_tool_name,
                "arguments": arguments,
                "result": result,
            }
        )
        if resolved_tool_name == "calendar.create_event" and isinstance(result, dict) and "id" in result:
            self._created_event_ids.append(result["id"])
        return resolved_tool_name, arguments, result

    def default_final_response(self) -> str:
        return fallback_final_response(self._tool_calls)

    def finish(self, final_response: str) -> SessionResult:
        self._trace_events.append(
            {
                "type": "session_complete",
                "session_id": self.session.session_id,
                "final_response": final_response,
            }
        )
        return SessionResult(
            final_response=final_response,
            tool_calls=list(self._tool_calls),
            created_event_ids=list(self._created_event_ids),
            trace_events=list(self._trace_events),
        )

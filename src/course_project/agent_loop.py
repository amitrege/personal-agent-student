from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .config import Settings
from .student_api import StudentRuntime, load_student_agent
from .worlds.factory import build_world


@dataclass
class SessionRun:
    session_id: str
    user_message: str
    final_response: str
    tool_calls: list[dict[str, Any]]
    created_event_ids: list[str]
    trace_events: list[dict[str, Any]]


def run_scenario(
    *,
    scenario: dict[str, Any],
    user_id: str,
    settings: Settings,
    model_client: Any,
) -> dict[str, Any]:
    run_dir = _make_run_dir(settings.artifacts_dir, scenario["id"], user_id)
    world = build_world(scenario, user_id)
    session_runs: list[SessionRun] = []
    score: dict[str, Any] | None = None
    final_state: dict[str, Any] | None = None

    try:
        student_agent = load_student_agent(settings)
        for session in scenario["users"][user_id]["sessions"]:
            world.start_session(session["session_id"])
            runtime = StudentRuntime(
                scenario=scenario,
                world=world,
                model_client=model_client,
                settings=settings,
                user_id=user_id,
                session=session,
            )
            student_result = student_agent.run_session(runtime.session, runtime)
            session_runs.append(
                SessionRun(
                    session_id=session["session_id"],
                    user_message=session["user_message"],
                    final_response=student_result.final_response,
                    tool_calls=student_result.tool_calls,
                    created_event_ids=student_result.created_event_ids,
                    trace_events=student_result.trace_events,
                )
            )
        score = world.evaluate_run(session_runs)
        final_state = world.snapshot()
    finally:
        world.close()

    assert score is not None
    assert final_state is not None
    trace_events = [event for session_run in session_runs for event in session_run.trace_events]
    _write_jsonl(run_dir / "trace.jsonl", trace_events)
    _write_json(run_dir / "final_state.json", final_state)
    _write_json(run_dir / "score.json", score)

    return {
        "scenario_id": scenario["id"],
        "user_id": user_id,
        "run_dir": str(run_dir),
        "score": score,
        "sessions": [
            {
                "session_id": item.session_id,
                "final_response": item.final_response,
                "created_event_ids": item.created_event_ids,
                "tool_calls": item.tool_calls,
            }
            for item in session_runs
        ],
    }


def _make_run_dir(base_dir: Path, scenario_id: str, user_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    run_dir = base_dir / scenario_id / user_id / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event))
            handle.write("\n")


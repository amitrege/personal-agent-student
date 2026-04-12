from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from typing import Any

from .agent_loop import run_scenario
from .config import load_settings
from .llm.factory import make_client
from .scenarios.loader import available_scenarios, evaluate_results, load_scenario
from .social_market import DEFAULT_SOCIAL_AGENTS, run_social_market


GRADE_STAGES = (
    {
        "id": "stage1",
        "label": "Stage 1",
        "scenario": "tool_use_stage_v1",
        "agent_module": "student_scaffold.agent",
        "weight": 40.0,
    },
    {
        "id": "stage2",
        "label": "Stage 2",
        "scenario": "memory_stage_v1",
        "agent_module": "student_scaffold_stage2.agent",
        "weight": 25.0,
    },
    {
        "id": "stage3",
        "label": "Stage 3",
        "scenario": "learned_memory_stage_v1",
        "agent_module": "student_scaffold_stage3.agent",
        "weight": 35.0,
    },
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Course project stage-1 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Validate local model connectivity")
    doctor.add_argument("--prompt", default="Reply with READY.", help="Prompt to use for the smoke check")
    doctor.add_argument("--client", default="local", choices=("local", "scripted"))

    run = subparsers.add_parser("run", help="Run one scenario for one user")
    run.add_argument("--scenario", default="tool_use_stage_v1", choices=available_scenarios())
    run.add_argument("--user", required=True)
    run.add_argument("--client", default="local", choices=("local", "scripted"))

    evaluate = subparsers.add_parser("eval", help="Evaluate all users in a scenario")
    evaluate.add_argument("--scenario", default="tool_use_stage_v1", choices=available_scenarios())
    evaluate.add_argument("--client", default="local", choices=("local", "scripted"))
    evaluate.add_argument(
        "--show-cases",
        action="store_true",
        help="Include prompt, expected event, actual event, and tool sequence for every case.",
    )
    evaluate.add_argument(
        "--show-failures",
        action="store_true",
        help="Include prompt, expected event, actual event, and tool sequence for failed cases only.",
    )

    grade = subparsers.add_parser("grade", help="Estimate visible project grade across stages")
    grade.add_argument("--client", default="local", choices=("local", "scripted"))
    grade.add_argument("--stage1-agent", default="student_scaffold.agent")
    grade.add_argument("--stage2-agent", default="student_scaffold_stage2.agent")
    grade.add_argument("--stage3-agent", default="student_scaffold_stage3.agent")

    train = subparsers.add_parser("train-preference-extractor", help="Train the Stage-3 preference extractor")
    train.add_argument("--training-data", default=None)
    train.add_argument("--model-path", default=None)
    train.add_argument("--max-ngram", type=int, default=2)

    social = subparsers.add_parser("social-market", help="Run the scheduling-only simulated user market")
    social.add_argument("--scenario", default="social_market_v1", choices=available_scenarios())
    social.add_argument("--client", default="local", choices=("local", "scripted"))
    social.add_argument("--agents", nargs="+", default=list(DEFAULT_SOCIAL_AGENTS))

    return parser


def _cmd_doctor(args: argparse.Namespace) -> int:
    settings = load_settings()
    print(f"env_file={settings.env_file}")
    print("env_files=" + ",".join(str(path) for path in settings.env_files))
    print(f"llamacpp_base_url={settings.llamacpp_base_url}")
    print(f"llamacpp_model={settings.llamacpp_model}")
    print(f"local_context_window={settings.local_context_window}")
    print(f"local_max_tokens={settings.local_max_tokens}")
    client = make_client(args.client, settings)
    response = client.complete(
        messages=[{"role": "user", "content": args.prompt}],
        require_json=False,
    )
    print("assistant_response=" + response.content.strip())
    print("assistant_model=" + response.model)
    print("doctor_client=" + args.client)
    print("doctor_status=ok")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    settings = load_settings()
    scenario = load_scenario(args.scenario)
    if args.user not in scenario["users"]:
        raise SystemExit(
            f"Unknown user '{args.user}'. Valid users: {', '.join(sorted(scenario['users']))}"
        )
    client = make_client(args.client, settings)
    result = run_scenario(
        scenario=scenario,
        user_id=args.user,
        settings=settings,
        model_client=client,
    )
    print(json.dumps(result, indent=2))
    return 0


def _cmd_eval(args: argparse.Namespace) -> int:
    settings = load_settings()
    scenario = load_scenario(args.scenario)
    client = make_client(args.client, settings)
    results = {}
    for user_id in sorted(scenario["users"]):
        results[user_id] = run_scenario(
            scenario=scenario,
            user_id=user_id,
            settings=settings,
            model_client=client,
        )
    summary = evaluate_results(scenario, results)
    if args.show_cases or args.show_failures:
        summary["case_details"] = _case_details(
            scenario=scenario,
            results=results,
            failures_only=bool(args.show_failures),
        )
        memory_details = _memory_details(
            scenario=scenario,
            results=results,
            failures_only=bool(args.show_failures),
        )
        if memory_details:
            summary["memory_details"] = memory_details
    print(json.dumps(summary, indent=2))
    return 0


def _case_details(
    *,
    scenario: dict[str, Any],
    results: dict[str, dict[str, Any]],
    failures_only: bool,
) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for user_id in sorted(scenario["users"]):
        user = scenario["users"][user_id]
        result = results[user_id]
        score_sessions = result["score"].get("sessions", {})
        run_sessions = {item["session_id"]: item for item in result.get("sessions", [])}
        for session in user["sessions"]:
            session_id = session["session_id"]
            checks = dict(score_sessions.get(session_id, {}))
            failed = not _session_passed(checks)
            if failures_only and not failed:
                continue
            run_session = run_sessions.get(session_id, {})
            tool_calls = list(run_session.get("tool_calls", []))
            details.append(
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "failed": failed,
                    "user_message": session.get("user_message", ""),
                    "artifact": session.get("artifact", {}),
                    "expected_event": _expected_event(session),
                    "actual_event": _last_created_event(tool_calls),
                    "create_event_results": _create_event_results(tool_calls),
                    "checks": checks,
                    "tool_sequence": [str(call.get("name", "")) for call in tool_calls],
                    "final_response": run_session.get("final_response", ""),
                    "run_dir": result.get("run_dir", ""),
                }
            )
    return details


def _session_passed(checks: dict[str, Any]) -> bool:
    if checks.get("correct_event") is not True:
        return False
    if checks.get("read_artifact") is not True:
        return False
    if checks.get("preferred_start") and checks.get("preferred_start_correct") is not True:
        return False
    return True


def _expected_event(session: dict[str, Any]) -> dict[str, Any]:
    task = dict(session.get("task", {}))
    expected = dict(session.get("expected", {}).get("event", {}))
    return {
        "title": task.get("title"),
        "date": task.get("date"),
        "duration_minutes": task.get("duration_minutes"),
        "attendees": task.get("attendees", []),
        "valid_starts": expected.get("valid_starts", []),
        "preferred_start": expected.get("preferred_start"),
    }


def _create_event_results(tool_calls: list[dict[str, Any]]) -> list[Any]:
    return [
        call.get("result")
        for call in tool_calls
        if call.get("name") == "calendar.create_event"
    ]


def _last_created_event(tool_calls: list[dict[str, Any]]) -> Any:
    for result in reversed(_create_event_results(tool_calls)):
        if isinstance(result, dict) and "id" in result:
            return result
    return None


def _memory_details(
    *,
    scenario: dict[str, Any],
    results: dict[str, dict[str, Any]],
    failures_only: bool,
) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for user_id in sorted(scenario["users"]):
        user = scenario["users"][user_id]
        expected_memories = list(user.get("expected_memories", []))
        if not expected_memories:
            continue
        memory = dict(results[user_id]["score"].get("memory", {}))
        expected_count = int(memory.get("expected_count", len(expected_memories)))
        correct_count = int(memory.get("correct_count", 0))
        failed = correct_count < expected_count
        if failures_only and not failed:
            continue
        details.append(
            {
                "user_id": user_id,
                "failed": failed,
                "expected_memories": expected_memories,
                "memory_results": memory.get("results", []),
                "stored_memories": memory.get("stored", []),
            }
        )
    return details


def _stage_grade_score(stage_id: str, summary: dict[str, Any]) -> float:
    suite_score = float(summary.get("suite_score", 0.0))
    if stage_id == "stage1":
        return suite_score
    required_scores = [
        suite_score,
        100.0 * float(summary.get("preference_accuracy", 0.0)),
        100.0 * float(summary.get("memory_accuracy", 0.0)),
    ]
    return min(required_scores)


def _evaluate_stage(
    *,
    base_settings: Any,
    model_client: Any,
    stage: dict[str, Any],
    agent_module: str,
) -> dict[str, Any]:
    scenario = load_scenario(str(stage["scenario"]))
    settings = replace(base_settings, student_agent_module=agent_module)
    results = {}
    for user_id in sorted(scenario["users"]):
        results[user_id] = run_scenario(
            scenario=scenario,
            user_id=user_id,
            settings=settings,
            model_client=model_client,
        )
    summary = evaluate_results(scenario, results)
    stage_id = str(stage["id"])
    suite_score = float(summary.get("suite_score", 0.0))
    grade_score = _stage_grade_score(stage_id, summary)
    weight = float(stage["weight"])
    metrics = {key: value for key, value in summary.items() if key != "users"}
    return {
        "label": stage["label"],
        "scenario": stage["scenario"],
        "agent_module": agent_module,
        "weight": weight,
        "suite_score": round(suite_score, 2),
        "grade_score": round(grade_score, 2),
        "weighted_points": round(weight * grade_score / 100.0, 2),
        "metrics": metrics,
    }


def _cmd_grade(args: argparse.Namespace) -> int:
    settings = load_settings()
    client = make_client(args.client, settings)
    agent_modules = {
        "stage1": args.stage1_agent,
        "stage2": args.stage2_agent,
        "stage3": args.stage3_agent,
    }
    stages: dict[str, dict[str, Any]] = {}
    total_points = 0.0

    for stage in GRADE_STAGES:
        stage_id = str(stage["id"])
        agent_module = str(agent_modules[stage_id])
        try:
            stage_result = _evaluate_stage(
                base_settings=settings,
                model_client=client,
                stage=stage,
                agent_module=agent_module,
            )
        except Exception as exc:  # noqa: BLE001 - keep grade usable while code is in progress.
            stage_result = {
                "label": stage["label"],
                "scenario": stage["scenario"],
                "agent_module": agent_module,
                "weight": stage["weight"],
                "suite_score": 0.0,
                "grade_score": 0.0,
                "weighted_points": 0.0,
                "error": str(exc),
            }
        total_points += float(stage_result["weighted_points"])
        stages[stage_id] = stage_result

    result = {
        "visible_only": True,
        "warning": (
            "This is a visible-benchmark estimate. Hidden grading scenarios may use "
            "different users, artifacts, and preference phrasings."
        ),
        "client": args.client,
        "details": "Run bash launch eval, bash launch stage2-eval, or bash launch stage3-eval for per-user breakdowns.",
        "grade_policy": {
            "stage1": 40.0,
            "stage2": 25.0,
            "stage3": 35.0,
            "formula": "sum(stage_weight * stage_grade_score / 100)",
            "stage_grade_score": {
                "stage1": "suite_score",
                "stage2": "min(suite_score, 100 * preference_accuracy, 100 * memory_accuracy)",
                "stage3": "min(suite_score, 100 * preference_accuracy, 100 * memory_accuracy)",
            },
        },
        "stages": stages,
        "visible_grade_points": round(total_points, 2),
        "visible_grade_percent": round(total_points, 2),
    }
    print(json.dumps(result, indent=2))
    return 0


def _cmd_train_preference_extractor(args: argparse.Namespace) -> int:
    try:
        from .learned.preference_extractor import (
            default_model_path,
            default_training_path,
            train_preference_extractor,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The instructor preference-extractor training helper is not included in this distribution. "
            "For Stage 3, write and run your own training script inside student_scaffold_stage3/."
        ) from exc

    settings = load_settings()
    if args.training_data:
        training_path = Path(args.training_data)
    else:
        root = Path(settings.root)
        training_path = default_training_path(root)
    model_path = Path(args.model_path) if args.model_path else default_model_path(settings.root)
    result = train_preference_extractor(
        training_path=training_path,
        model_path=model_path,
        max_ngram=args.max_ngram,
    )
    print(json.dumps(result, indent=2))
    return 0


def _cmd_social_market(args: argparse.Namespace) -> int:
    settings = load_settings()
    result = run_social_market(
        scenario_name=args.scenario,
        agent_modules=list(args.agents),
        settings=settings,
        client_name=args.client,
    )
    print(json.dumps(result, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return _cmd_doctor(args)
        if args.command == "run":
            return _cmd_run(args)
        if args.command == "eval":
            return _cmd_eval(args)
        if args.command == "grade":
            return _cmd_grade(args)
        if args.command == "train-preference-extractor":
            return _cmd_train_preference_extractor(args)
        if args.command == "social-market":
            return _cmd_social_market(args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    return 1

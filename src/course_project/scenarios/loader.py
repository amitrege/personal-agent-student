from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCENARIO_ROOT = Path(__file__).resolve().parent


def available_scenarios() -> tuple[str, ...]:
    names = sorted(path.parent.name for path in SCENARIO_ROOT.glob("*/scenario.json"))
    return tuple(names)


def load_scenario(name: str) -> dict[str, Any]:
    path = SCENARIO_ROOT / name / "scenario.json"
    if not path.exists():
        raise FileNotFoundError(f"Unknown scenario: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_results(
    scenario: dict[str, Any],
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    user_ids = sorted(results)
    per_user = {user_id: results[user_id]["score"] for user_id in user_ids}
    suite_score = round(
        sum(item["total"] for item in per_user.values()) / max(len(per_user), 1),
        2,
    )
    artifact_read_rate = round(
        sum(item["artifact_read_rate"] for item in per_user.values()) / max(len(per_user), 1),
        2,
    )
    event_accuracy = round(
        sum(item["event_accuracy"] for item in per_user.values()) / max(len(per_user), 1),
        2,
    )
    summary = {
        "scenario_id": scenario["id"],
        "users": per_user,
        "suite_score": suite_score,
        "artifact_read_rate": artifact_read_rate,
        "event_accuracy": event_accuracy,
    }
    for metric in ("preference_accuracy", "memory_accuracy"):
        values = [
            item[metric]
            for item in per_user.values()
            if isinstance(item.get(metric), (int, float))
        ]
        if values:
            summary[metric] = round(sum(values) / len(values), 2)
    return summary

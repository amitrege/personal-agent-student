from __future__ import annotations

from dataclasses import replace
from typing import Any

from .agent_loop import run_scenario
from .config import Settings
from .llm.factory import make_client
from .scenarios.loader import load_scenario


DEFAULT_SOCIAL_AGENTS = (
    "student_scaffold_stage3.agent",
)


def run_social_market(
    *,
    scenario_name: str,
    agent_modules: list[str],
    settings: Settings,
    client_name: str,
) -> dict[str, Any]:
    scenario = load_scenario(scenario_name)
    user_ids = sorted(scenario["users"])
    client = make_client(client_name, settings)
    raw_results: dict[str, dict[str, dict[str, Any]]] = {}

    for agent_module in agent_modules:
        agent_settings = replace(
            settings,
            student_agent_module=agent_module,
            memory_mode="full",
        )
        raw_results[agent_module] = {}
        for user_id in user_ids:
            raw_results[agent_module][user_id] = run_scenario(
                scenario=scenario,
                user_id=user_id,
                settings=agent_settings,
                model_client=client,
            )

    users: dict[str, Any] = {}
    agent_summaries: dict[str, Any] = {
        agent_module: {
            "users_won": 0,
            "popularity_votes": 0,
            "average_satisfaction": 0.0,
            "average_preference_accuracy": 0.0,
            "average_event_accuracy": 0.0,
        }
        for agent_module in agent_modules
    }

    for user_id in user_ids:
        ranked_agents = sorted(
            agent_modules,
            key=lambda agent_module: _winner_key(raw_results[agent_module][user_id]["score"]),
            reverse=True,
        )
        best_key = _winner_key(raw_results[ranked_agents[0]][user_id]["score"])
        top_agents = [
            agent_module
            for agent_module in ranked_agents
            if _winner_key(raw_results[agent_module][user_id]["score"]) == best_key
        ]
        vote_share = 1 / max(len(top_agents), 1)
        for agent_module in top_agents:
            agent_summaries[agent_module]["users_won"] += vote_share
            agent_summaries[agent_module]["popularity_votes"] += vote_share
        users[user_id] = {
            "winner": top_agents[0] if len(top_agents) == 1 else None,
            "top_agents": top_agents,
            "ranked_agents": ranked_agents,
            "scores": {
                agent_module: _public_score(raw_results[agent_module][user_id]["score"])
                for agent_module in agent_modules
            },
        }

    for agent_module in agent_modules:
        scores = [raw_results[agent_module][user_id]["score"] for user_id in user_ids]
        agent_summaries[agent_module]["average_satisfaction"] = _mean(score["total"] for score in scores)
        agent_summaries[agent_module]["average_preference_accuracy"] = _mean(
            score.get("preference_accuracy", 0.0) for score in scores
        )
        agent_summaries[agent_module]["average_event_accuracy"] = _mean(
            score.get("event_accuracy", 0.0) for score in scores
        )

    market_rank = sorted(
        agent_modules,
        key=lambda agent_module: (
            agent_summaries[agent_module]["users_won"],
            agent_summaries[agent_module]["average_satisfaction"],
            agent_summaries[agent_module]["average_preference_accuracy"],
            agent_summaries[agent_module]["average_event_accuracy"],
        ),
        reverse=True,
    )
    return {
        "scenario_id": scenario["id"],
        "client": client_name,
        "users": users,
        "agents": agent_summaries,
        "market_rank": market_rank,
        "winner": market_rank[0] if market_rank else None,
    }


def _winner_key(score: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        float(score.get("total", 0.0)),
        float(score.get("preference_accuracy", 0.0)),
        float(score.get("memory_accuracy", 0.0)),
        float(score.get("event_accuracy", 0.0)),
    )


def _public_score(score: dict[str, Any]) -> dict[str, Any]:
    public_score = {
        "satisfaction": score.get("total", 0.0),
        "event_accuracy": score.get("event_accuracy", 0.0),
        "artifact_read_rate": score.get("artifact_read_rate", 0.0),
        "preference_accuracy": score.get("preference_accuracy", 0.0),
    }
    if "memory_accuracy" in score:
        public_score["memory_accuracy"] = score["memory_accuracy"]
    return public_score


def _mean(values: Any) -> float:
    items = [float(value) for value in values]
    if not items:
        return 0.0
    return round(sum(items) / len(items), 2)

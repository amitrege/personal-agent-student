from __future__ import annotations

from typing import Any

from .base import WorldAdapter
from .campus_tools import CampusToolsWorld


def build_world(scenario: dict[str, Any], user_id: str) -> WorldAdapter:
    world_type = scenario.get("world", "campus_tools")
    if world_type == "campus_tools":
        return CampusToolsWorld(scenario, user_id)
    raise ValueError(f"Unsupported world type: {world_type}")

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ModelResponse:
    content: str
    reasoning_details: Any | None
    raw_response: dict[str, Any]
    model: str


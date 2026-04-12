from __future__ import annotations

from typing import Any

from ..config import Settings
from .local_openai import LocalOpenAIClient
from .scripted import ScriptedToolUseClient


def make_client(client_name: str, settings: Settings) -> Any:
    if client_name == "scripted":
        return ScriptedToolUseClient()
    if client_name == "local":
        return LocalOpenAIClient(settings)
    raise ValueError(f"Unsupported client: {client_name}")


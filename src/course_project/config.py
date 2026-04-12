from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


DEFAULT_LLAMACPP_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_LLAMACPP_MODEL = "local-model"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env(name: str, default: str, loaded: dict[str, str]) -> str:
    return os.environ.get(name, loaded.get(name, default))


def _env_int(name: str, default: int, loaded: dict[str, str]) -> int:
    return int(_env(name, str(default), loaded))


def _env_bool(name: str, default: bool, loaded: dict[str, str]) -> bool:
    raw = _env(name, "true" if default else "false", loaded).strip().lower()
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    root: Path
    env_file: Path
    env_files: tuple[Path, ...]
    artifacts_dir: Path
    llamacpp_base_url: str
    llamacpp_model: str
    llamacpp_api_key: str
    local_context_window: int
    local_max_tokens: int
    local_timeout_seconds: int
    max_model_turns: int
    max_tool_calls: int
    max_completion_tokens: int
    compact_local_prompt: bool
    student_agent_module: str
    memory_mode: str
    preference_model_path: str

    @property
    def llamacpp_chat_url(self) -> str:
        return self.llamacpp_base_url.rstrip("/") + "/chat/completions"

    def local_ready(self) -> bool:
        return bool(self.llamacpp_base_url.strip() and self.llamacpp_model.strip())


def load_settings(root: Path | None = None) -> Settings:
    root_dir = root or project_root()
    env_file = root_dir / ".env"
    colab_env_file = root_dir / ".env.colab"
    env_files = tuple(path for path in (env_file, colab_env_file) if path.exists())
    loaded: dict[str, str] = {}
    for path in env_files:
        loaded.update(_parse_dotenv(path))
    return Settings(
        root=root_dir,
        env_file=env_file,
        env_files=env_files,
        artifacts_dir=root_dir / "runs",
        llamacpp_base_url=_env("LLAMACPP_BASE_URL", DEFAULT_LLAMACPP_BASE_URL, loaded),
        llamacpp_model=_env("LLAMACPP_MODEL", DEFAULT_LLAMACPP_MODEL, loaded),
        llamacpp_api_key=_env("LLAMACPP_API_KEY", "", loaded),
        local_context_window=_env_int("LOCAL_CONTEXT_WINDOW", 4096, loaded),
        local_max_tokens=_env_int("LOCAL_MAX_TOKENS", 512, loaded),
        local_timeout_seconds=_env_int("LOCAL_TIMEOUT_SECONDS", 120, loaded),
        max_model_turns=_env_int("MAX_MODEL_TURNS", 6, loaded),
        max_tool_calls=_env_int("MAX_TOOL_CALLS", 6, loaded),
        max_completion_tokens=_env_int("MAX_COMPLETION_TOKENS", 512, loaded),
        compact_local_prompt=_env_bool("COMPACT_LOCAL_PROMPT", True, loaded),
        student_agent_module=_env("STUDENT_AGENT_MODULE", "student_scaffold.agent", loaded),
        memory_mode=_env("MEMORY_MODE", "full", loaded),
        preference_model_path=_env("PREFERENCE_MODEL_PATH", "", loaded),
    )

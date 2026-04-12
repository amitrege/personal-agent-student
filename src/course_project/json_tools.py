from __future__ import annotations

import json
import re
from typing import Any

from .worlds.base import ToolSpec, WorldAdapter


def build_json_tools_prompt(
    *,
    rules: list[str],
    tools: list[ToolSpec],
    compact: bool,
) -> str:
    response_contract = {
        "tool_call": {"name": tools[0].name if tools else "tool.name", "arguments": {}},
        "final_response": "",
        "final_explanation": "",
    }
    if compact:
        compact_tools = [compact_tool_prompt_entry(spec) for spec in tools]
        return (
            "\n".join(rules)
            + "\nAvailable tools: "
            + json.dumps(compact_tools, separators=(",", ":"))
            + "\nPut all tool parameter values under tool_call.arguments only."
            + "\nReturn exactly one tool_call or one final_response."
        )
    return (
        "\n".join(rules)
        + "\n\nAvailable tools:\n"
        + json.dumps(
            [
                {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                }
                for spec in tools
            ],
            indent=2,
        )
        + "\n\nReply schema example:\n"
        + json.dumps(response_contract, indent=2)
    )


def parse_action(content: str) -> dict[str, Any]:
    candidate = extract_json_object(content)
    action = json.loads(candidate)
    action = normalize_action(action)
    if "tool_call" not in action:
        action["tool_call"] = None
    if "final_response" not in action:
        action["final_response"] = ""
    if "final_explanation" not in action:
        action["final_explanation"] = ""
    return action


def normalize_action(action: dict[str, Any]) -> dict[str, Any]:
    if "final_response" not in action:
        for alias in ("answer", "response", "message"):
            if isinstance(action.get(alias), str):
                action["final_response"] = action[alias]
                break

    tool_call = action.get("tool_call")
    if isinstance(tool_call, str):
        parsed = try_parse_json_like(tool_call)
        action["tool_call"] = parsed if isinstance(parsed, dict) else None
        tool_call = action.get("tool_call")

    if isinstance(tool_call, dict):
        if "name" not in tool_call:
            for alias in ("tool", "tool_name", "function", "action"):
                if isinstance(tool_call.get(alias), str):
                    tool_call["name"] = tool_call[alias]
                    break
        merged_arguments: dict[str, Any] = {}
        for alias in (
            "required_args",
            "optional_args",
            "required_parameters",
            "optional_parameters",
            "args",
            "parameters",
            "params",
        ):
            merged_arguments.update(coerce_argument_mapping(tool_call.get(alias)))
        merged_arguments.update(coerce_argument_mapping(tool_call.get("arguments")))
        tool_call["arguments"] = merged_arguments

    if action.get("tool_call") is not None and not isinstance(action["tool_call"], dict):
        action["tool_call"] = None
    action["final_response"] = coerce_action_text(action.get("final_response"))
    action["final_explanation"] = coerce_action_text(action.get("final_explanation"))
    return action


def extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Could not find JSON object in model response: {text}")
    return match.group(0)


def try_parse_json_like(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
        stripped = stripped.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return stripped


def coerce_argument_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        parsed = try_parse_json_like(value)
        if isinstance(parsed, dict):
            return parsed
    return {}


def coerce_action_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def serialize_feedback_payload(value: Any) -> str:
    return json.dumps(compact_feedback_value(value), sort_keys=True)


def compact_feedback_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= 3:
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): compact_feedback_value(item, depth=depth + 1)
            for key, item in value.items()
        }
    if isinstance(value, list):
        limited_items = value[:8]
        compacted = [compact_feedback_value(item, depth=depth + 1) for item in limited_items]
        if len(value) > len(limited_items):
            compacted.append({"_truncated_items": len(value) - len(limited_items)})
        return compacted
    if isinstance(value, str) and len(value) > 600:
        return value[:450] + " ...[truncated]... " + value[-120:]
    return value


def compact_tool_prompt_entry(spec: ToolSpec) -> dict[str, Any]:
    required_parameters = []
    optional_parameters = []
    for name, meta in spec.parameters.items():
        if isinstance(meta, dict) and meta.get("required"):
            required_parameters.append(name)
        else:
            optional_parameters.append(name)
    entry = {"name": spec.name}
    if required_parameters:
        entry["required_parameters"] = required_parameters
    if optional_parameters:
        entry["optional_parameters"] = optional_parameters[:4]
    return entry


def resolve_tool_name(world: WorldAdapter, tool_name: Any) -> str:
    normalized = str(tool_name).strip().strip("`")
    normalized = re.sub(r"\(\)$", "", normalized)
    available = [spec.name for spec in world.list_tools()]
    if normalized in available:
        return normalized
    bare_name = normalized.rsplit(".", 1)[-1]
    matches = [name for name in available if name.rsplit(".", 1)[-1] == bare_name]
    if len(matches) == 1:
        return matches[0]
    return normalized


def fallback_final_response(tool_calls: list[dict[str, Any]]) -> str:
    if not tool_calls:
        return ""
    last_tool_call = tool_calls[-1]
    tool_name = str(last_tool_call.get("name") or "tool")
    result = last_tool_call.get("result")
    if tool_name == "calendar.create_event" and isinstance(result, dict):
        title = result.get("title")
        start_time = result.get("start_time")
        date = result.get("date")
        if isinstance(title, str) and isinstance(start_time, str) and isinstance(date, str):
            return f"Scheduled '{title}' on {date} at {start_time}."
    return f"Completed the requested action using {tool_name}."


def invalid_json_feedback() -> str:
    return (
        "Your previous reply was not valid complete JSON. "
        "Reply again with one compact JSON object only and keep it shorter."
    )


def missing_finish_feedback() -> str:
    return "Your previous reply did not finish the task. Reply with valid JSON only."


def exhausted_invalid_feedback() -> str:
    return "I couldn't complete the requested task."


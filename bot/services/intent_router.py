from __future__ import annotations

import json
import re
import sys

from services.llm_client import LLMError, get_llm_client
from services.lms_client import BackendError, get_lms_client


SYSTEM_PROMPT = """
You are an LMS analytics bot.

Your job is to help the user using backend tools whenever data is needed.
Prefer tool usage over guessing.

Rules:
- If the user asks about labs, students, scores, pass rates, groups, completion, timelines, or rankings, use tools.
- If the user asks a multi-step question, use multiple tools as needed.
- If the user greets you, respond briefly and explain what you can do.
- If the input is ambiguous, ask a clarifying question.
- If the input is gibberish or meaningless, respond helpfully and suggest example questions.
- Use concise, factual answers grounded in tool results.
- Do not invent data.
"""


def get_tool_schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_items",
                "description": "List labs and tasks available in the LMS.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_learners",
                "description": "Get enrolled learners and their groups.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_scores",
                "description": "Get score distribution for a lab in 4 buckets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. lab-04",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_pass_rates",
                "description": "Get per-task average scores and attempt counts for a lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. lab-04",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_timeline",
                "description": "Get per-day submission activity for a lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. lab-04",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_groups",
                "description": "Get per-group performance and student counts for a lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. lab-04",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_top_learners",
                "description": "Get top learners by score for a lab or overall. Limit controls how many learners to return.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Optional lab identifier, e.g. lab-04",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of learners to return",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_completion_rate",
                "description": "Get completion rate percentage for a lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. lab-04",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "trigger_sync",
                "description": "Refresh LMS data from the autochecker pipeline.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]


def _extract_lab_id(text: str) -> str | None:
    match = re.search(r"lab[\s-]?(\d+)", text.lower())
    if not match:
        return None
    return f"lab-{int(match.group(1)):02d}"


def execute_tool(name: str, arguments: dict) -> dict:
    client = get_lms_client()

    if name == "get_items":
        data = client.get_json("/items/")
        return {"tool": name, "data": data}

    if name == "get_learners":
        data = client.get_json("/learners/")
        return {"tool": name, "data": data}

    if name == "get_scores":
        data = client.get_json("/analytics/scores", params={"lab": arguments["lab"]})
        return {"tool": name, "lab": arguments["lab"], "data": data}

    if name == "get_pass_rates":
        data = client.get_json(
            "/analytics/pass-rates",
            params={"lab": arguments["lab"]},
        )
        return {"tool": name, "lab": arguments["lab"], "data": data}

    if name == "get_timeline":
        data = client.get_json(
            "/analytics/timeline",
            params={"lab": arguments["lab"]},
        )
        return {"tool": name, "lab": arguments["lab"], "data": data}

    if name == "get_groups":
        data = client.get_json(
            "/analytics/groups",
            params={"lab": arguments["lab"]},
        )
        return {"tool": name, "lab": arguments["lab"], "data": data}

    if name == "get_top_learners":
        params = {}
        if arguments.get("lab"):
            params["lab"] = arguments["lab"]
        if arguments.get("limit") is not None:
            params["limit"] = arguments["limit"]
        data = client.get_json("/analytics/top-learners", params=params)
        return {"tool": name, "params": params, "data": data}

    if name == "get_completion_rate":
        data = client.get_json(
            "/analytics/completion-rate",
            params={"lab": arguments["lab"]},
        )
        return {"tool": name, "lab": arguments["lab"], "data": data}

    if name == "trigger_sync":
        data = client.post_json("/pipeline/sync", payload={})
        return {"tool": name, "data": data}

    raise ValueError(f"Unknown tool: {name}")


def route_natural_language(user_text: str) -> str:
    text = user_text.strip()

    if not text:
        return "Please send a message. I can help with labs, learners, scores, and rankings."

    llm = get_llm_client()
    tools = get_tool_schemas()

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]

    # Small helper for very short ambiguous inputs like "lab 4"
    guessed_lab = _extract_lab_id(text)
    if guessed_lab and len(text.split()) <= 3 and "?" not in text:
        return (
            f"What would you like to know about {guessed_lab}?\n"
            "I can show scores, pass rates, groups, timeline, completion rate, or top learners."
        )

    try:
        for _ in range(8):
            response = llm.chat(messages=messages, tools=tools)
            choice = response["choices"][0]["message"]

            tool_calls = choice.get("tool_calls") or []

            if tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": choice.get("content") or "",
                        "tool_calls": tool_calls,
                    }
                )

                for call in tool_calls:
                    tool_name = call["function"]["name"]
                    raw_args = call["function"].get("arguments") or "{}"

                    try:
                        tool_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        tool_args = {}

                    print(
                        f"[tool] LLM called: {tool_name}({json.dumps(tool_args, ensure_ascii=False)})",
                        file=sys.stderr,
                    )

                    try:
                        result = execute_tool(tool_name, tool_args)
                    except BackendError as exc:
                        result = {"tool": tool_name, "error": str(exc)}
                    except Exception as exc:
                        result = {"tool": tool_name, "error": f"Tool execution error: {exc}"}

                    result_json = json.dumps(result, ensure_ascii=False)

                    data = result.get("data")
                    if isinstance(data, list):
                        size_info = f"{len(data)} items"
                    elif isinstance(data, dict):
                        size_info = f"{len(data)} fields"
                    else:
                        size_info = "result received"

                    print(f"[tool] Result: {size_info}", file=sys.stderr)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "name": tool_name,
                            "content": result_json,
                        }
                    )

                print(
                    f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM",
                    file=sys.stderr,
                )
                continue

            content = (choice.get("content") or "").strip()
            if content:
                return content

            return (
                "I couldn't produce a final answer.\n"
                "Try asking about labs, learners, groups, completion rate, or scores."
            )

        return "I reached the tool-call limit while reasoning. Please try a more specific question."

    except LLMError as exc:
        return str(exc)

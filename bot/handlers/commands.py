from __future__ import annotations

from services.lms_client import BackendError, get_lms_client


def handle_start() -> str:
    return (
        "Welcome to the LMS bot!\n"
        "I can show backend health, available labs, and pass rates.\n"
        "Use /help to see available commands."
    )


def handle_help() -> str:
    return (
        "Available commands:\n"
        "/start - welcome message\n"
        "/help - list commands\n"
        "/health - check backend status\n"
        "/labs - list available labs\n"
        "/scores <lab-id> - show pass rates for a lab"
    )


def handle_health() -> str:
    client = get_lms_client()
    try:
        items = client.get_json("/items/")
        count = len(items) if isinstance(items, list) else 0
        return f"Backend is healthy. {count} items available."
    except BackendError as exc:
        return str(exc)


def handle_labs() -> str:
    client = get_lms_client()
    try:
        items = client.get_json("/items/")
    except BackendError as exc:
        return str(exc)

    if not isinstance(items, list):
        return "Backend error: unexpected response format from /items/."

    labs = [item for item in items if item.get("type") == "lab"]

    if not labs:
        return "No labs found in backend data."

    labs_sorted = sorted(labs, key=lambda x: x.get("title", ""))

    lines = ["Available labs:"]
    for lab in labs_sorted:
        title = lab.get("title", "Untitled lab")
        lines.append(f"- {title}")

    return "\n".join(lines)


def handle_scores(lab_id: str) -> str:
    client = get_lms_client()
    try:
        scores = client.get_json("/analytics/pass-rates", params={"lab": lab_id})
    except BackendError as exc:
        return str(exc)

    if not isinstance(scores, list):
        return "Backend error: unexpected response format from /analytics/pass-rates."

    if not scores:
        return (
            f"No scores found for {lab_id}.\n"
            "Check the lab id and try /labs."
        )

    lines = [f"Pass rates for {lab_id}:"]
    for row in scores:
        task = row.get("task", "Unknown task")
        avg_score = row.get("avg_score", 0.0)
        attempts = row.get("attempts", 0)
        lines.append(f"- {task}: {avg_score}% ({attempts} attempts)")

    return "\n".join(lines)


def handle_unknown(user_input: str) -> str:
    return (
        f"Unknown command: {user_input}\n"
        "Use /help to see available commands."
    )

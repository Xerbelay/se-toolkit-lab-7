def handle_start() -> str:
    return (
        "Welcome to the LMS bot!\n"
        "Use /help to see available commands."
    )


def handle_help() -> str:
    return (
        "Available commands:\n"
        "/start - welcome message\n"
        "/help - list commands\n"
        "/health - backend status\n"
        "/labs - list labs\n"
        "/scores <lab-id> - pass rates for a lab"
    )


def handle_health() -> str:
    return "Health check is not implemented yet."


def handle_labs() -> str:
    return "Labs listing is not implemented yet."


def handle_scores(lab_id: str) -> str:
    return f"Scores for {lab_id} are not implemented yet."


def handle_unknown(user_input: str) -> str:
    return f"Unknown command: {user_input}"

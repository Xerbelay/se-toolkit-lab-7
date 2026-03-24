import argparse
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import get_settings
from handlers.commands import (
    handle_health,
    handle_help,
    handle_labs,
    handle_scores,
    handle_start,
    handle_unknown,
)


def route_input(user_input: str) -> str:
    text = user_input.strip()

    if text == "/start":
        return handle_start()

    if text == "/help":
        return handle_help()

    if text == "/health":
        return handle_health()

    if text == "/labs":
        return handle_labs()

    if text.startswith("/scores"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "Usage: /scores <lab-id>"
        return handle_scores(parts[1])

    return handle_unknown(text)


async def run_telegram_bot() -> None:
    settings = get_settings()

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is missing in .env.bot.secret")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start_command(message: Message) -> None:
        await message.answer(handle_start())

    @dp.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(handle_help())

    @dp.message(Command("health"))
    async def health_command(message: Message) -> None:
        await message.answer(handle_health())

    @dp.message(Command("labs"))
    async def labs_command(message: Message) -> None:
        await message.answer(handle_labs())

    @dp.message(Command("scores"))
    async def scores_command(message: Message) -> None:
        parts = message.text.split(maxsplit=1) if message.text else []
        if len(parts) < 2:
            await message.answer("Usage: /scores <lab-id>")
            return
        await message.answer(handle_scores(parts[1]))

    @dp.message()
    async def fallback_command(message: Message) -> None:
        text = message.text or ""
        await message.answer(handle_unknown(text))

    await dp.start_polling(bot)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        type=str,
        help="Run bot in CLI test mode with the provided input",
    )
    args = parser.parse_args()

    if args.test is not None:
        response = route_input(args.test)
        print(response)
        return

    asyncio.run(run_telegram_bot())


if __name__ == "__main__":
    main()

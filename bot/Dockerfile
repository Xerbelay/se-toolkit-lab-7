FROM ghcr.io/astral-sh/uv:python3.14-bookworm

WORKDIR /app

COPY bot /app
COPY uv.lock /app/uv.lock

RUN uv sync --frozen --no-dev

CMD ["uv", "run", "bot.py"]

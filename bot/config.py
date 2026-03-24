from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str | None = None

    lms_api_base_url: str = "http://localhost:42002"
    lms_api_key: str = "change-me"

    llm_api_base_url: str = "http://localhost:42005/v1"
    llm_api_key: str | None = None
    llm_api_model: str = "coder-model"

    model_config = SettingsConfigDict(
        env_file="../.env.bot.secret",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()

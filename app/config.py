from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    brave_api_key: str
    openai_model: str = "gpt-4.1-mini"
    max_search_results: int = 8
    max_pages_to_scrape: int = 6
    request_timeout_seconds: int = 20
    user_agent: str = "AgenticSearchChallenge/1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

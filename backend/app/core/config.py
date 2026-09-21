from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Indian Stock Market Analyzer"
    app_version: str = "0.1.0"
    debug: bool = False
    allowed_origins: str = "http://localhost:5173"

    upstox_client_id: str | None = None
    upstox_client_secret: str | None = None
    upstox_redirect_uri: str | None = None
    upstox_access_token: str | None = None

    news_api_key: str | None = None
    gnews_api_key: str | None = None
    openai_api_key: str | None = None
    database_url: str = "sqlite:///./market_analyzer.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str = "sqlite:///./dev.db"
    SECRET_KEY: str = "dev_secret_key_change_me_32_chars_min__"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_DEV_MODE: bool = True
    CORS_ORIGINS: str = ""
    START_BALANCE: int = 5000
    SEASON_GOAL: int = 50000
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    @property
    def cors_list(self) -> list[str]:
        if not self.CORS_ORIGINS.strip():
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

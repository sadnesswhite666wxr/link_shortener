from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LinkStat"
    APP_PORT: int = 6060
    APP_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES_MIN: int = 30
    METRICS_PATH: str = "/metrics"
    redis_ttl_sec: int = 3600
    DB_ADMIN_USERNAME: str
    DB_ADMIN_PASSWORD: str
    DB_ADMIN_EMAIL: str
    DB_USER_USERNAME: str
    DB_USER_PASSWORD: str
    DB_USER_EMAIL: str
    DB_URL: str
    REDIS_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

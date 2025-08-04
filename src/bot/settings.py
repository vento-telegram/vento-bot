from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES__",
        env_file=".env",
        extra="ignore",
    )

    URI: PostgresDsn
    MIGRATION_TIMEOUT: int = 30


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )
    MAIN_TOKEN: str
    POSTGRES: PostgresSettings = PostgresSettings()


settings = Settings()

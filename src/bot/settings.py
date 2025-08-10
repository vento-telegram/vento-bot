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


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPENAI__",
        env_file=".env",
        extra="ignore",
    )
    API_KEY: str


## Removed Lava payments settings


class VeoSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VEO__",
        env_file=".env",
        extra="ignore",
    )
    NEXUS_API_KEY: str = ""


class KieSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KIE__",
        env_file=".env",
        extra="ignore",
    )
    # NOTE: override via env KIE__API_KEY in production
    API_KEY: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )
    MAIN_TOKEN: str
    WELCOME_BONUS_AMOUNT: int = 150
    # Removed external payments webhook
    POSTGRES: PostgresSettings = PostgresSettings()
    OPENAI: OpenAISettings = OpenAISettings()
    VEO: VeoSettings = VeoSettings()
    KIE: KieSettings = KieSettings()


settings = Settings()

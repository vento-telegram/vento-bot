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


class LavaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LAVA__",
        env_file=".env",
        extra="ignore",
    )
    API_KEY: str


class VeoSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VEO__",
        env_file=".env",
        extra="ignore",
    )
    NEXUS_API_KEY: str = ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )
    MAIN_TOKEN: str
    WELCOME_BONUS_AMOUNT: int = 150
    PAYMENTS_WEBHOOK_API_KEY: str
    POSTGRES: PostgresSettings = PostgresSettings()
    OPENAI: OpenAISettings = OpenAISettings()
    LAVA: LavaSettings = LavaSettings()
    VEO: VeoSettings = VeoSettings()


settings = Settings()

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

class YookassaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="YOOKASSA__",
        env_file=".env",
        extra="ignore",
    )
    SHOP_ID: str
    SECRET_KEY: str

class BepaidSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BEPAID__",
        env_file=".env",
        extra="ignore",
    )
    SHOP_ID: str | None = None
    TOKEN: str | None = None

class KIESettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KIE__",
        env_file=".env",
        extra="ignore",
    )
    API_KEY: str
    BASE_URL: str = "https://api.kie.ai"
    CALLBACK_BASE: str = "https://bukhavets.com"


class NexusSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEXUS__",
        env_file=".env",
        extra="ignore",
    )
    API_KEY: str | None = None
    BASE_URL: str = "https://nexusapi.dev"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )
    MAIN_TOKEN: str
    POSTGRES: PostgresSettings = PostgresSettings()
    OPENAI: OpenAISettings = OpenAISettings()
    YOOKASSA: YookassaSettings = YookassaSettings()
    BEPAID: BepaidSettings = BepaidSettings()
    KIE: KIESettings = KIESettings()
    NEXUS: NexusSettings = NexusSettings()
    WEB_PORT: int = 8080


settings = Settings()

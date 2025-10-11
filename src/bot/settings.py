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
    SHOP_ID: str
    TOKEN: str


class KieSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KIE__",
        env_file=".env",
        extra="ignore",
    )
    API_KEY: str
    BASE_URL: str


class NexusSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEXUS__",
        env_file=".env",
        extra="ignore",
    )
    API_KEY: str
    BASE_URL: str


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="REDIS__",
        env_file=".env",
    )

    HOST: str
    PORT: int
    PASSWORD: str = ""


class WebhooksSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WEBHOOKS__",
        env_file=".env",
    )
    BASE_URL: str
    PORT: int = 8080

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )
    MAIN_TOKEN: str
    ADMIN_TOKEN: str
    SUPPORT_USERNAME: str
    POSTGRES: PostgresSettings = PostgresSettings()
    OPENAI: OpenAISettings = OpenAISettings()
    YOOKASSA: YookassaSettings = YookassaSettings()
    BEPAID: BepaidSettings = BepaidSettings()
    KIE: KieSettings = KieSettings()
    NEXUS: NexusSettings = NexusSettings()
    REDIS: RedisSettings = RedisSettings()
    WEBHOOKS: WebhooksSettings = WebhooksSettings()


settings = Settings()

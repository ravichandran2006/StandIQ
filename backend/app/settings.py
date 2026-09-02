from functools import lru_cache
from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    app_name: str = "standiq-api"
    app_version: str = "v1"
    app_env: str = "development"
    database_url: SecretStr | None = None
    pinecone_api_key: SecretStr | None = None
    pinecone_index_name: str | None = None
    llm_provider: str | None = None
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    app_secret_key: SecretStr | None = None
    log_level: LogLevel = "INFO"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def database_configured(self) -> bool:
        return bool(self.database_url and self.database_url.get_secret_value().strip())

    def pinecone_configured(self) -> bool:
        return bool(
            self.pinecone_api_key
            and self.pinecone_api_key.get_secret_value().strip()
            and self.pinecone_index_name
            and self.pinecone_index_name.strip()
        )

    def llm_configured(self) -> bool:
        return bool(
            self.llm_provider
            and self.llm_api_key
            and self.llm_api_key.get_secret_value().strip()
            and self.llm_model
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

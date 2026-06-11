from dataclasses import dataclass
from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    db: str
    url: str


@dataclass(frozen=True)
class APIConfig:
    title: str
    description: str
    version: str
    prefix: str
    port: int


@dataclass(frozen=True)
class SecurityConfig:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "cic"
    postgres_password: str = "cic"
    postgres_db: str = "cic_digital"
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    postgres_read_user: str = "cic_read"
    postgres_read_password: str = "cic_read"
    database_read_url: str | None = Field(
        default=None, validation_alias="DATABASE_READ_URL"
    )

    api_title: str = "CIC Digital"
    api_description: str = "API de leitura do Catecismo da Igreja Católica"
    api_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    def _build_database_url(self, user: str, password: str) -> str:
        return (
            f"postgresql+psycopg2://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database(self) -> DatabaseConfig:
        """Conexão admin — Alembic, seeds e manutenção futura."""
        url = self.database_url or self._build_database_url(
            self.postgres_user, self.postgres_password
        )
        return DatabaseConfig(
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_user,
            password=self.postgres_password,
            db=self.postgres_db,
            url=url,
        )

    @property
    def database_read(self) -> DatabaseConfig:
        """Conexão read-only — padrão da API e rotas de leitura."""
        url = self.database_read_url or self._build_database_url(
            self.postgres_read_user, self.postgres_read_password
        )
        return DatabaseConfig(
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_read_user,
            password=self.postgres_read_password,
            db=self.postgres_db,
            url=url,
        )

    @property
    def api(self) -> APIConfig:
        return APIConfig(
            title=self.api_title,
            description=self.api_description,
            version=self.api_version,
            prefix=self.api_prefix,
            port=self.api_port,
        )

    @property
    def security(self) -> SecurityConfig:
        return SecurityConfig(
            secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
            access_token_expire_minutes=self.jwt_access_token_expire_minutes,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _build_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    user = os.getenv("POSTGRES_USER", "cic")
    password = os.getenv("POSTGRES_PASSWORD", "cic")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "cic_digital")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


@dataclass(frozen=True)
class Settings:
    database_url: str
    postgres_host: str
    postgres_port: str
    postgres_db: str
    postgres_user: str


settings = Settings(
    database_url=_build_database_url(),
    postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
    postgres_port=os.getenv("POSTGRES_PORT", "5432"),
    postgres_db=os.getenv("POSTGRES_DB", "cic_digital"),
    postgres_user=os.getenv("POSTGRES_USER", "cic"),
)

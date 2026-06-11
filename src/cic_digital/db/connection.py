from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from cic_digital.core.config import settings


class Database:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )

    def dispose(self) -> None:
        self.engine.dispose()

    def ping(self) -> bool:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True


db = Database(settings.database_read.url)
admin_db = Database(settings.database.url)


def get_db() -> Generator[Session, None, None]:
    session = db.session_factory()
    try:
        yield session
    finally:
        session.close()

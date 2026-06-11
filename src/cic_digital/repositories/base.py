from sqlalchemy.orm import Session


class BaseRepository:
    """Classe base para repositories — recebe Session via construtor."""

    def __init__(self, session: Session) -> None:
        self._session = session

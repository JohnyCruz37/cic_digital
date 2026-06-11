from cic_digital.repositories.base import BaseRepository


class BaseService:
    """Classe base para services — injeta repository no construtor."""

    def __init__(self, repository: BaseRepository) -> None:
        self._repository = repository

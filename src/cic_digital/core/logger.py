import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

LOG_FORMAT: Final = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
LOGGER_PREFIX: Final = "cic_digital"

_configured = False


def setup_logger(level: str, log_file: str) -> None:
    """Configura logging da aplicação — chamar apenas em main.py."""
    global _configured
    if _configured:
        return

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger(LOGGER_PREFIX)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    if name.startswith(LOGGER_PREFIX):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_PREFIX}.{name}")

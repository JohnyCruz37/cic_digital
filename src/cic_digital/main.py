"""Ponto de entrada — uvicorn cic_digital.main:app"""

from cic_digital.core.config import settings
from cic_digital.core.logger import setup_logger

setup_logger(level=settings.log_level, log_file=settings.log_file)

from cic_digital.api.factory import create_app

app = create_app()

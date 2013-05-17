import logging
from models import Log


class SQLHandler(logging.Handler):

    def emit(self, record):
        Log.objects.create(
            message=record.getMessage(), level=record.levelname,
            logger=record.name
        )

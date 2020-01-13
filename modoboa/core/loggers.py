import logging


class SQLHandler(logging.Handler):

    def emit(self, record):
        from .models import Log

        Log.objects.create(
            message=record.getMessage(), level=record.levelname,
            logger=record.name
        )

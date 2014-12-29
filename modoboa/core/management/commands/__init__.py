"""
Extra classes for management commands.
"""

from django.db import connection


class CloseConnectionMixin(object):

    """
    A simple mixin used to close all database connections after
    command execution.
    """

    def execute(self, *args, **options):
        """Execute will call handle so we can close the connection here."""
        super(CloseConnectionMixin, self).execute(*args, **options)
        connection.close()

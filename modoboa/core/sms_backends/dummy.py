"""Dummy SMS backend."""

from . import SMSBackend


class DUMMYBackend(SMSBackend):
    """Dummy backend to use with tests."""

    def send(self, text, recipients):
        """Print text on stdout."""
        print(text)
        return True

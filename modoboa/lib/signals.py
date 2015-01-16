"""Custom signals."""

from django.dispatch import Signal

request_accessor = Signal()


def get_request():
    """Get the current request from anywhere."""
    return request_accessor.send(None)[0][1]

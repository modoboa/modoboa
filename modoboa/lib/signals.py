"""Custom signals."""

from threading import local

_local_store = local()


def set_current_request(request):
    """Store current request."""
    _local_store.request = request


def get_request():
    """Get the current request from anywhere."""
    if "request" not in _local_store.__dict__:
        return None
    return _local_store.request

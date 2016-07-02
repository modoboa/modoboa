"""Custom signals."""

import django.dispatch

request_accessor = django.dispatch.Signal()


def get_request():
    """Get the current request from anywhere."""
    request = request_accessor.send(None)
    if request:
        return request[0][1]
    return None

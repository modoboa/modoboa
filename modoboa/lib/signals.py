"""Custom signals."""

from threading import local

import django.dispatch

request_accessor = local()
request_accessor.signal = django.dispatch.Signal()


def get_request():
    """Get the current request from anywhere."""
    request = request_accessor.signal.send(None)
    if request:
        return request[0][1]
    return None

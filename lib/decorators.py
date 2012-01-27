# coding: utf-8
"""
:mod:`decorators` --- common decorators
---------------------------------------
"""
from functools import wraps
from exceptions import NeedsMailboxException

def needs_mailbox():
    """Check if the current user owns at least one mailbox

    Some applications (the webmail for example) need a mailbox to
    work.
    """
    def decorator(f):
        @wraps(f)
        def wrapped_f(request, *args, **kwargs):
            if request.user.has_mailbox:
                return f(request, *args, **kwargs)
            raise NeedsMailboxException()
        return wrapped_f
    return decorator

"""Calendar backend definition."""

from importlib import import_module


class CalendarBackend:
    """Base backend class."""

    def __init__(self, calendar=None):
        """Default constructor."""
        self.calendar = calendar

    def create_event(self, event):
        """Create a new event."""
        raise NotImplementedError

    def get_event(self, uid):
        """Retrieve an even using its uid."""
        raise NotImplementedError

    def get_events(self, start, end):
        """Retrieve a list of event."""
        raise NotImplementedError

    def delete_event(self, uid):
        """Delete an event using its uid."""
        raise NotImplementedError


def get_backend(name, *args, **kwargs):
    """Return a backend instance."""
    module = import_module(f"modoboa.calendars.backends.{name}")
    return getattr(module, f"{name.capitalize()}Backend")(*args, **kwargs)


def get_backend_from_request(name, request, calendar=None):
    """Return a backend instance from a request."""
    return get_backend(name, request.user.email, request.auth, calendar=calendar)

"""Radicale test mocks."""

from caldav import Event
from caldav.lib.url import URL


EV1 = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp.//CalDAV Client//EN
BEGIN:VEVENT
UID:20010712T182145Z-123401@example.com
DTSTAMP:20060712T182145Z
DTSTART:20060714T170000Z
DTEND:20060715T040000Z
SUMMARY:Bastille Day Party
END:VEVENT
END:VCALENDAR
"""

EV2 = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp.//CalDAV Client//EN
BEGIN:VEVENT
UID:20010712T182145Z-123401@example.com
DTSTAMP:20070712T182145Z
DTSTART:20070714T170000Z
DTEND:20070715T040000Z
SUMMARY:Bastille Day Party +1year
END:VEVENT
END:VCALENDAR
"""


class Response:
    """Fake requests response."""

    def __init__(self, status):
        self.status = status
        self.raw = ""


class DAVClientMock:
    """Mock class for DAVClient instance."""

    url = URL.objectify("http://localhost")

    def mkcalendar(self, url):
        return True

    def delete(self, url):
        return True

    def proppatch(self, url, body, dummy=None):
        return Response(200)

    def request(self, url, method="GET", body="", headers=None):
        return Response(200)


class Calendar:

    def __init__(self, client=None, url=None, parent=None, name=None, id=None, **extra):
        self.url = URL.objectify(url or "http://localhost/calendar")
        self.client = DAVClientMock()

    def add_event(self, data):
        return True

    def save_event(self, *args, **kwargs):
        return True

    def event_by_url(self, url):
        res = Event(url=url, data=EV1, parent=self)
        return res

    def search(self, **kwargs):
        return [
            Event(data=EV1, parent=self),
            Event(data=EV2, parent=self),
        ]

    def set_properties(self, properties):
        return True

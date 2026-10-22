"""Fetch the external iCalendar feeds users subscribe to."""

import hashlib
import ipaddress

import icalendar
import recurring_ical_events
import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

from django.core.cache import cache
from django.utils.translation import gettext as _

from .backends.caldav_ import get_event_dates

#: Seconds a fetched feed is kept in cache
CACHE_TIMEOUT = 15 * 60
#: Seconds to wait for the remote server (connection and each read)
FETCH_TIMEOUT = 10
MAX_FEED_SIZE = 10 * 1024 * 1024
MAX_REDIRECTS = 5


class FeedError(Exception):
    """A feed can't be fetched or parsed."""


class PublicAddressMixin:
    """Refuse connections to non public addresses (SSRF protection).

    The check is made on the address the socket is connected to, so it
    also applies to redirects and can't be bypassed by DNS rebinding.
    """

    def _new_conn(self):
        sock = super()._new_conn()
        address = ipaddress.ip_address(sock.getpeername()[0])
        if address.version == 6 and address.ipv4_mapped:
            address = address.ipv4_mapped
        if not address.is_global:
            sock.close()
            raise OSError(f"Connection to non public address {address} refused")
        return sock


class PublicHTTPConnection(PublicAddressMixin, HTTPConnection):
    pass


class PublicHTTPSConnection(PublicAddressMixin, HTTPSConnection):
    pass


class PublicHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = PublicHTTPConnection


class PublicHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = PublicHTTPSConnection


class PublicAddressAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        super().init_poolmanager(*args, **kwargs)
        self.poolmanager.pool_classes_by_scheme = {
            "http": PublicHTTPConnectionPool,
            "https": PublicHTTPSConnectionPool,
        }


def download_feed(url):
    """Download a feed, refusing non public addresses and big files."""
    session = requests.Session()
    # A proxy would hide the address really connected to
    session.trust_env = False
    session.max_redirects = MAX_REDIRECTS
    session.mount("http://", PublicAddressAdapter())
    session.mount("https://", PublicAddressAdapter())
    try:
        with session.get(url, timeout=FETCH_TIMEOUT, stream=True) as resp:
            resp.raise_for_status()
            content = b""
            for chunk in resp.iter_content(chunk_size=65536):
                content += chunk
                if len(content) > MAX_FEED_SIZE:
                    raise FeedError(_("The calendar is too big"))
    except requests.RequestException as exc:
        raise FeedError(_("Unable to fetch the calendar")) from exc
    return content


def get_feed(url):
    """Return the parsed feed found at url, fetched at most every CACHE_TIMEOUT."""
    key = f"calendars:subscription:{hashlib.sha256(url.encode()).hexdigest()}"
    content = cache.get(key)
    if content is not None:
        return icalendar.Calendar.from_ical(content)
    content = download_feed(url)
    try:
        feed = icalendar.Calendar.from_ical(content)
    except ValueError as exc:
        raise FeedError(_("The calendar is not a valid iCalendar file")) from exc
    cache.set(key, content, CACHE_TIMEOUT)
    return feed


def get_events(subscription, start, end):
    """Return the events of a subscription between start and end.

    Recurring events are expanded.
    """
    try:
        occurrences = recurring_ical_events.of(get_feed(subscription.url)).between(
            start, end
        )
    except (ValueError, recurring_ical_events.InvalidCalendar) as exc:
        raise FeedError(_("The calendar is not a valid iCalendar file")) from exc
    events = []
    for occurrence in occurrences:
        attendees = occurrence.get("attendee", [])
        if not isinstance(attendees, list):
            attendees = [attendees]
        event = {
            "id": str(occurrence.get("uid", "")),
            "title": str(occurrence.get("summary", "")),
            "color": subscription.color,
            "description": str(occurrence.get("description", "")),
            "calendar": subscription,
            "attendees": [
                {
                    "display_name": str(attendee.params.get("CN", "")),
                    "email": str(attendee)
                    .removeprefix("mailto:")
                    .removeprefix("MAILTO:"),
                }
                for attendee in attendees
            ],
            # No recurrence_id: it is only used to modify an occurrence, and
            # recurring_ical_events sets one on every occurrence anyway
        }
        # recurring_ical_events always sets DTEND on occurrences
        event.update(
            get_event_dates(occurrence.decoded("dtstart"), occurrence.decoded("dtend"))
        )
        events.append(event)
    return events

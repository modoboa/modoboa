"""CalDAV calendar backend."""

import datetime
import uuid

import caldav
from caldav.elements import dav, ical
from caldav import Calendar
from dateutil.relativedelta import relativedelta
import icalendar
import vobject

from django.utils import timezone
from django.utils.encoding import smart_str

from modoboa.parameters import tools as param_tools

from . import CalendarBackend, RECURRENCE_FREQUENCIES


def same_date(value1, value2):
    """Compare two dates or datetimes, possibly using different timezones."""
    if isinstance(value1, datetime.datetime) != isinstance(value2, datetime.datetime):
        return False
    if isinstance(value1, datetime.datetime) and (
        (value1.tzinfo is None) != (value2.tzinfo is None)
    ):
        return value1.replace(tzinfo=None) == value2.replace(tzinfo=None)
    return value1 == value2


def convert_date(value, reference):
    """Convert value to the type (and timezone) used by reference."""
    if not isinstance(reference, datetime.datetime):
        return value.date() if isinstance(value, datetime.datetime) else value
    if not isinstance(value, datetime.datetime):
        return datetime.datetime.combine(value, datetime.time.min).replace(
            tzinfo=reference.tzinfo
        )
    if reference.tzinfo is None:
        return value.replace(tzinfo=None)
    if value.tzinfo is None:
        return value.replace(tzinfo=reference.tzinfo)
    return value.astimezone(reference.tzinfo)


def get_vevent_end(vevent):
    """Return the end of a vevent (DTEND is optional)."""
    if "dtend" in vevent.contents:
        return vevent.dtend.value
    if "duration" in vevent.contents:
        return vevent.dtstart.value + vevent.duration.value
    if isinstance(vevent.dtstart.value, datetime.datetime):
        return vevent.dtstart.value
    return vevent.dtstart.value + datetime.timedelta(days=1)


def get_event_dates(start, end):
    """Return the allDay, start and end values expected by the calendar view."""
    if isinstance(start, datetime.datetime):
        return {"allDay": False, "start": start, "end": end}
    tz = timezone.get_current_timezone()
    return {
        "allDay": True,
        "start": datetime.datetime.combine(start, datetime.time.min).replace(tzinfo=tz),
        # Small back to make vuetify calendar happy. 'All day' events are generally
        # created from one day to the day after (even for a 1 day duration...)
        "end": datetime.datetime.combine(
            end - relativedelta(days=1), datetime.time.min
        ).replace(tzinfo=tz),
    }


def set_vevent_dates(vevent, start=None, end=None):
    """Replace the dates of a vevent."""
    if start is not None:
        del vevent.contents["dtstart"]
        vevent.add("dtstart").value = start
    if end is not None:
        vevent.contents.pop("duration", None)
        vevent.contents.pop("dtend", None)
        vevent.add("dtend").value = end


def get_requested_dates(data):
    """Return the (start, end) dates of an event, as stored in iCalendar."""
    if data.get("allDay"):
        # DTEND is exclusive for all day events (see create_event)
        return data["start_date"], data["end_date"] + relativedelta(days=1)
    return data.get("start"), data.get("end")


def get_master(vcal):
    """Return the main vevent of an event (the one without RECURRENCE-ID)."""
    for vevent in vcal.vevent_list:
        if "recurrence-id" not in vevent.contents:
            return vevent
    return vcal.vevent_list[0]


def get_overrides(vcal):
    """Return the vevents overriding an occurrence of a recurring event."""
    return [vevent for vevent in vcal.vevent_list if "recurrence-id" in vevent.contents]


def find_override(vcal, recurrence_id):
    """Return the vevent overriding the given occurrence, if any."""
    for vevent in get_overrides(vcal):
        if same_date(vevent.recurrence_id.value, recurrence_id):
            return vevent
    return None


def get_recurrence(vevent):
    """Return the recurrence rule of a vevent, as exposed by the API."""
    rrules = vevent.contents.get("rrule", [])
    if not rrules:
        return None
    rule = icalendar.vRecur.from_ical(rrules[0].value)
    frequency = rule["FREQ"][0]
    until = rule.get("UNTIL", [None])[0]
    return {
        "frequency": frequency,
        "until": until.isoformat() if until else None,
        # Rules the API cannot represent must not be overwritten by clients
        "custom": (
            len(rrules) > 1
            or "rdate" in vevent.contents
            or frequency not in RECURRENCE_FREQUENCIES
            or bool(set(rule) - {"FREQ", "UNTIL"})
        ),
    }


def get_until(until, dtstart):
    """Return the UNTIL value matching the type of DTSTART (RFC 5545)."""
    if not isinstance(dtstart, datetime.datetime):
        return until.date() if isinstance(until, datetime.datetime) else until
    if not isinstance(until, datetime.datetime):
        until = datetime.datetime.combine(
            until, datetime.time(23, 59, 59), tzinfo=dtstart.tzinfo
        )
    if dtstart.tzinfo is None:
        return until.replace(tzinfo=None)
    return until.astimezone(datetime.timezone.utc)


def build_rrule(recurrence, dtstart):
    """Return the RRULE (as a dict) of an API recurrence rule."""
    rule = {"FREQ": recurrence["frequency"]}
    if recurrence.get("until"):
        rule["UNTIL"] = get_until(recurrence["until"], dtstart)
    return rule


def set_recurrence(vcal, recurrence):
    """Replace the recurrence rule of an event (None removes it)."""
    master = get_master(vcal)
    old = get_recurrence(master)
    master.contents.pop("rrule", None)
    master.contents.pop("rdate", None)
    until = None
    if recurrence:
        rule = build_rrule(recurrence, master.dtstart.value)
        master.add("rrule").value = icalendar.vRecur(rule).to_ical().decode()
        if old and old["frequency"] == recurrence["frequency"]:
            until = rule.get("UNTIL")
            if until is None:
                return
    # Exceptions no longer match an occurrence: drop them
    for vevent in get_overrides(vcal):
        if until is None or convert_date(vevent.recurrence_id.value, until) > until:
            vcal.remove(vevent)
    exdates = master.contents.pop("exdate", [])
    if until is None:
        return
    for exdate in exdates:
        exdate.value = [
            value for value in exdate.value if convert_date(value, until) <= until
        ]
        if exdate.value:
            master.add(exdate)


class Caldav_Backend(CalendarBackend):
    """CalDAV calendar backend."""

    def __init__(self, username, password, calendar=None):
        """Constructor."""
        super().__init__(calendar)
        server_url = smart_str(param_tools.get_global_parameter("server_location"))
        # Send credentials preemptively: otherwise the first request is sent
        # anonymously and Radicale answers 401 after its anti-bruteforce
        # delay ([auth] delay, ~1s), which is paid on every API call.
        self.client = caldav.DAVClient(
            server_url, username=username, password=str(password), auth_type="basic"
        )
        if self.calendar:
            self.remote_cal = Calendar(self.client, calendar.encoded_path)

    def _event_url(self, uid):
        """Return the URL of an event in the current calendar."""
        return f"{self.remote_cal.url.geturl()}/{uid}.ics"

    def _serialize_event(self, vevent):
        """Convert a vevent to a dictionary."""
        description = (
            vevent.description.value if "description" in vevent.contents else ""
        )
        # Expanded occurrences of a recurring event all carry a RECURRENCE-ID
        recurrence_id = (
            vevent.recurrence_id.value.isoformat()
            if "recurrence-id" in vevent.contents
            else None
        )
        result = {
            "id": vevent.uid.value,
            "title": vevent.summary.value,
            "color": self.calendar.color,
            "description": description,
            "calendar": self.calendar,
            "attendees": [],
            "recurrence_id": recurrence_id,
        }
        result.update(get_event_dates(vevent.dtstart.value, get_vevent_end(vevent)))
        if "attendee" in vevent.contents:
            for attendee in vevent.contents["attendee"]:
                email = attendee.value.replace("mailto:", "").replace("MAILTO:", "")
                cn = attendee.params.get("CN")
                result["attendees"].append(
                    {"display_name": cn[0] if cn else "", "email": email}
                )
        return result

    def create_calendar(self, url):
        """Create a new calendar."""
        self.client.mkcalendar(url)

    def update_calendar(self, calendar):
        """Update an existing calendar."""
        remote_cal = Calendar(self.client, calendar.encoded_path)
        remote_cal.set_properties(
            [dav.DisplayName(calendar.name), ical.CalendarColor(calendar.color)]
        )

    def create_event(self, data):
        """Create a new event."""
        uid = uuid.uuid4()
        if not data["allDay"]:
            dtstart = data["start"]
            dtend = data["end"]
        else:
            dtstart = data["start_date"]
            # Ensure consistent behavior with other calendar clients (like TB.)
            dtend = data["end_date"] + relativedelta(days=1)
        rrule = (
            build_rrule(data["recurrence"], dtstart) if data.get("recurrence") else None
        )
        self.remote_cal.save_event(
            uid=uid, dtstart=dtstart, dtend=dtend, summary=data["title"], rrule=rrule
        )
        return uid

    def _update_vevent(self, vevent, data):
        """Apply modifications to a vevent."""
        if "title" in data:
            vevent.summary.value = data["title"]
        start, end = get_requested_dates(data)
        set_vevent_dates(vevent, start, end)
        if "description" in data:
            if "description" in vevent.contents:
                vevent.description.value = data["description"]
            else:
                vevent.add("description").value = data["description"]
        if "attendees" in data:
            if "attendee" in vevent.contents:
                del vevent.contents["attendee"]
            for attdef in data.get("attendees", []):
                attendee = vevent.add("attendee")
                attendee.value = "MAILTO:{}".format(attdef["email"])
                attendee.params["CN"] = [attdef["display_name"]]
                attendee.params["ROLE"] = ["REQ-PARTICIPANT"]

    def _get_or_create_override(self, vcal, recurrence_id):
        """Return the vevent overriding an occurrence, create it if needed."""
        override = find_override(vcal, recurrence_id)
        if override is not None:
            return override
        master = get_master(vcal)
        override = master.duplicate(master)
        for name in ("rrule", "rdate", "exdate"):
            override.contents.pop(name, None)
        start = convert_date(recurrence_id, master.dtstart.value)
        duration = get_vevent_end(master) - master.dtstart.value
        override.add("recurrence-id").value = start
        set_vevent_dates(override, start, start + duration)
        vcal.add(override)
        return override

    def _move_series(self, vcal, recurrence_id, data):
        """Move a whole series based on the new dates of one occurrence."""
        new_start, new_end = get_requested_dates(data)
        if new_start is None or new_end is None:
            return
        master = get_master(vcal)
        override = find_override(vcal, recurrence_id)
        if override is not None:
            occ_start = override.dtstart.value
            occ_end = get_vevent_end(override)
        else:
            occ_start = convert_date(recurrence_id, master.dtstart.value)
            occ_end = occ_start + (get_vevent_end(master) - master.dtstart.value)
        if isinstance(new_start, datetime.datetime) != isinstance(
            occ_start, datetime.datetime
        ):
            raise ValueError("Cannot change the all day status of a recurring event")
        if same_date(new_start, occ_start) and same_date(new_end, occ_end):
            return
        delta = new_start - occ_start
        start = master.dtstart.value + delta
        set_vevent_dates(master, start, start + (new_end - new_start))
        # Keep exceptions attached to the right occurrences
        for exdate in master.contents.get("exdate", []):
            exdate.value = [value + delta for value in exdate.value]
        for vevent in get_overrides(vcal):
            if same_date(vevent.dtstart.value, vevent.recurrence_id.value):
                # Occurrence not moved by the user: follow the series
                set_vevent_dates(
                    vevent,
                    vevent.dtstart.value + delta,
                    get_vevent_end(vevent) + delta,
                )
            vevent.recurrence_id.value += delta

    def update_event(self, uid, original_data):
        """Update an existing event.

        For a recurring event, ``recurrence_id`` identifies the modified
        occurrence and ``scope`` tells if the modification applies to this
        occurrence only or to the whole series.
        """
        data = dict(original_data)
        scope = data.pop("scope", None)
        recurrence_id = data.pop("recurrence_id", None)
        new_calendar = data.pop("calendar", None)
        update_rule = "recurrence" in data
        recurrence = data.pop("recurrence", None)
        url = self._event_url(uid)
        cal = self.remote_cal.event_by_url(url)
        vcal = cal.vobject_instance
        if recurrence_id and scope == "occurrence":
            self._update_vevent(self._get_or_create_override(vcal, recurrence_id), data)
        else:
            if recurrence_id and scope == "series":
                self._move_series(vcal, recurrence_id, data)
                for field in ("start", "end", "start_date", "end_date", "allDay"):
                    data.pop(field, None)
            self._update_vevent(get_master(vcal), data)
            if update_rule:
                set_recurrence(vcal, recurrence)
        if new_calendar and self.calendar.pk != new_calendar.pk:
            # Save the event in the new calendar before removing the old one,
            # so it is never lost.
            Calendar(self.client, new_calendar.encoded_path).add_event(vcal.serialize())
            self.remote_cal.client.delete(url)
        else:
            self.remote_cal.add_event(vcal.serialize())
        return uid

    def get_event(self, uid):
        """Retrieve and event using its uid."""
        event = self.remote_cal.event_by_url(self._event_url(uid))
        # Not expanded: return the series itself, with its recurrence rule
        master = get_master(event.vobject_instance)
        result = self._serialize_event(master)
        result["recurrence"] = get_recurrence(master)
        return result

    def get_events(self, start, end):
        """Retrieve a list of events (recurring events are expanded)."""
        orig_events = self.remote_cal.search(
            expand=True, start=start, end=end, event=True
        )
        events = []
        for event in orig_events:
            events.append(self._serialize_event(event.vobject_instance.vevent))
        return events

    def delete_event(self, uid, recurrence_id=None, scope=None):
        """Delete an event (or only one occurrence of it) using its uid."""
        url = self._event_url(uid)
        if not recurrence_id or scope != "occurrence":
            self.remote_cal.client.delete(url)
            return
        cal = self.remote_cal.event_by_url(url)
        vcal = cal.vobject_instance
        override = find_override(vcal, recurrence_id)
        if override is not None:
            vcal.remove(override)
        master = get_master(vcal)
        master.add("exdate").value = [convert_date(recurrence_id, master.dtstart.value)]
        self.remote_cal.add_event(vcal.serialize())

    def import_events(self, fp):
        """Import events from file."""
        content = smart_str(fp.read())
        counter = 0
        for cal in vobject.base.readComponents(content):
            for event in cal.vevent_list:
                ical = vobject.iCalendar()
                ical.add(event)
                self.remote_cal.add_event(ical.serialize())
                counter += 1
        return counter

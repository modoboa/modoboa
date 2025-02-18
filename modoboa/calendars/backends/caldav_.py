"""CalDAV calendar backend."""

import datetime
import uuid

import caldav
from caldav.elements import dav, ical
from caldav import Calendar
import vobject

from django.utils import timezone
from django.utils.encoding import smart_str

from modoboa.parameters import tools as param_tools

from . import CalendarBackend


class Caldav_Backend(CalendarBackend):
    """CalDAV calendar backend."""

    def __init__(self, username, password, calendar=None):
        """Constructor."""
        super().__init__(calendar)
        server_url = smart_str(param_tools.get_global_parameter("server_location"))
        self.client = caldav.DAVClient(server_url, username=username, password=password)
        if self.calendar:
            self.remote_cal = Calendar(self.client, calendar.encoded_path)

    def _serialize_event(self, event):
        """Convert a vevent to a dictionary."""
        vevent = event.vobject_instance.vevent
        description = (
            vevent.description.value if "description" in vevent.contents else ""
        )
        result = {
            "id": vevent.uid.value,
            "title": vevent.summary.value,
            "color": self.calendar.color,
            "description": description,
            "calendar": self.calendar,
            "attendees": [],
        }
        if isinstance(vevent.dtstart.value, datetime.datetime):
            all_day = False
            start = vevent.dtstart.value
            end = vevent.dtend.value
        else:
            tz = timezone.get_current_timezone()
            all_day = True
            start = datetime.datetime.combine(
                vevent.dtstart.value, datetime.time.min
            ).replace(tzinfo=tz)
            end = datetime.datetime.combine(
                vevent.dtend.value, datetime.time.min
            ).replace(tzinfo=tz)
        result.update({"allDay": all_day, "start": start, "end": end})
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
        cal = vobject.iCalendar()
        cal.add("vevent")
        cal.vevent.add("uid").value = str(uid)
        cal.vevent.add("summary").value = data["title"]
        if not data["allDay"]:
            cal.vevent.add("dtstart").value = data["start"]
            cal.vevent.add("dtend").value = data["end"]
        else:
            cal.vevent.add("dtstart").value = data["start"].date()
            cal.vevent.add("dtend").value = data["end"].date()
        self.remote_cal.add_event(cal)
        return uid

    def update_event(self, uid, original_data):
        """Update an existing event."""
        data = dict(original_data)
        url = f"{self.remote_cal.url.geturl()}/{uid}.ics"
        cal = self.remote_cal.event_by_url(url)
        orig_evt = cal.vobject_instance.vevent
        if "title" in data:
            orig_evt.summary.value = data["title"]
        if data.get("allDay"):
            data["start"] = data["start"].date()
            data["end"] = data["end"].date()
        if "start" in data:
            del orig_evt.contents["dtstart"]
            orig_evt.add("dtstart").value = data["start"]
        if "end" in data:
            del orig_evt.contents["dtend"]
            orig_evt.add("dtend").value = data["end"]
        if "description" in data:
            if "description" in orig_evt.contents:
                orig_evt.description.value = data["description"]
            else:
                orig_evt.add("description").value = data["description"]
        if "attendees" in data:
            if "attendee" in orig_evt.contents:
                del orig_evt.contents["attendee"]
            for attdef in data.get("attendees", []):
                attendee = orig_evt.add("attendee")
                attendee.value = "MAILTO:{}".format(attdef["email"])
                attendee.params["CN"] = [attdef["display_name"]]
                attendee.params["ROLE"] = ["REQ-PARTICIPANT"]
        if "calendar" in data and self.calendar.pk != data["calendar"].pk:
            # Calendar has been changed, remove old event first.
            self.remote_cal.client.delete(url)
            remote_cal = Calendar(self.client, data["calendar"].encoded_path)
            url = f"{remote_cal.url.geturl()}/{uid}.ics"
        else:
            remote_cal = self.remote_cal
        remote_cal.add_event(cal.instance)
        return uid

    def get_event(self, uid):
        """Retrieve and event using its uid."""
        url = f"{self.remote_cal.url.geturl()}/{uid}.ics"
        event = self.remote_cal.event_by_url(url)
        return self._serialize_event(event)

    def get_events(self, start, end):
        """Retrieve a list of events."""
        orig_events = self.remote_cal.date_search(start, end)
        events = []
        for event in orig_events:
            events.append(self._serialize_event(event))
        return events

    def delete_event(self, uid):
        """Delete an event using its uid."""
        url = f"{self.remote_cal.url.geturl()}/{uid}.ics"
        self.remote_cal.client.delete(url)

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

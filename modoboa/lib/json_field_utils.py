"""Utils regarding time management."""

import json

from django.core.serializers.json import DjangoJSONEncoder

from datetime import datetime, timezone


def datetime_to_json_tz_unaware(datetime_object=None):
    """Take a datetime object and convert it to YYYY-MM-DDT-HH:MM:SS."""
    if datetime_object is None:
        datetime_object = datetime.utcnow()
    datetime_object = datetime_object.astimezone(timezone.utc)
    return datetime_object.strftime("%Y-%m-%dT%H:%M:%S")


def json_to_datetime(datetime_string):
    """Take a string in the YYYY-MM-DDT-HH:MM:SS form
    and convert it to a datetime object."""
    if isinstance(datetime_string, datetime):
        return datetime_string
    return datetime.strptime(datetime_string,
                             "%Y-%m-%dT%H:%M:%S")


class JSONDatetimeEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return datetime_to_json_tz_unaware(obj)
        else:
            return super().default(obj)

"""Rename calendars sharing a name with another calendar of the same owner.

Required before adding the unique constraints on calendar names. Only
names change: paths, hence Radicale collections, are left untouched.
"""

from django.db import migrations

#: Maximum length of a calendar name
NAME_MAX_LENGTH = 200


def get_free_name(name, used_names):
    """Return a name not in used_names (lowercase), based on name."""
    counter = 2
    while True:
        suffix = f" ({counter})"
        candidate = name[: NAME_MAX_LENGTH - len(suffix)] + suffix
        if candidate.lower() not in used_names:
            return candidate
        counter += 1


def rename_duplicates(model, owner_field):
    """Rename calendars whose name is already used by an older calendar."""
    calendars = list(model.objects.order_by(owner_field, "pk"))
    # Existing names are reserved, so unique names are never changed
    used_names = {}
    for calendar in calendars:
        owner = getattr(calendar, owner_field)
        used_names.setdefault(owner, set()).add(calendar.name.lower())
    seen_names = {}
    for calendar in calendars:
        owner = getattr(calendar, owner_field)
        owner_seen_names = seen_names.setdefault(owner, set())
        if calendar.name.lower() in owner_seen_names:
            calendar.name = get_free_name(calendar.name, used_names[owner])
            calendar.save(update_fields=["name"])
            used_names[owner].add(calendar.name.lower())
        owner_seen_names.add(calendar.name.lower())


def rename_duplicate_calendars(apps, schema_editor):
    rename_duplicates(apps.get_model("calendars", "UserCalendar"), "mailbox_id")
    rename_duplicates(apps.get_model("calendars", "SharedCalendar"), "domain_id")


class Migration(migrations.Migration):

    dependencies = [
        ("calendars", "0007_calendar_name_validator"),
    ]

    operations = [
        migrations.RunPython(rename_duplicate_calendars, migrations.RunPython.noop),
    ]

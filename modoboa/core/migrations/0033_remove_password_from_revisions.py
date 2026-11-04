import json

from django.db import migrations


def remove_password_from_revisions(apps, schema_editor):
    """Strip password hashes from existing User versions."""
    Version = apps.get_model("reversion", "Version")
    versions = Version.objects.filter(
        content_type__app_label="core", content_type__model="user", format="json"
    )
    to_update = []
    for version in versions.iterator():
        data = json.loads(version.serialized_data)
        found = False
        for item in data:
            if item.get("fields", {}).pop("password", None) is not None:
                found = True
        if found:
            version.serialized_data = json.dumps(data)
            to_update.append(version)
        if len(to_update) >= 500:
            Version.objects.bulk_update(to_update, ["serialized_data"])
            to_update = []
    if to_update:
        Version.objects.bulk_update(to_update, ["serialized_data"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0032_objectaccess_core_object_content_6b9cf4_idx"),
        ("reversion", "0002_add_index_on_version_for_content_type_and_db"),
    ]

    operations = [
        migrations.RunPython(remove_password_from_revisions, migrations.RunPython.noop),
    ]

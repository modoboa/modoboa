from django.db import models, migrations

APPS = (
    ("modoboa_admin", "admin"),
    ("modoboa_admin_limits", "limits"),
    ("modoboa_admin_relaydomains", "relaydomains"),
)


def rename_parameters(apps, schema_editor):
    """Rename old parameters."""
    Parameter = apps.get_model("lib", "Parameter")
    UserParameter = apps.get_model("lib", "UserParameter")
    for oldapp, newapp in APPS:
        for p in Parameter.objects.filter(name__startswith=oldapp):
            p.name = p.name.replace(oldapp, newapp)
            p.save()
        for p in UserParameter.objects.filter(name__startswith=oldapp):
            p.name = p.name.replace(oldapp, newapp)
            p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('lib', '0002_rename_parameters'),
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(rename_parameters)
    ]

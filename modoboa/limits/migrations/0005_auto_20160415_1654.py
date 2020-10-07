from django.db import migrations

from .. import utils


def create_limits(apps, schema_editor):
    """Create limits for existing domains."""
    Domain = apps.get_model("admin", "Domain")
    DomainObjectLimit = apps.get_model("limits", "DomainObjectLimit")
    to_create = []
    for domain in Domain.objects.all():
        for name, tpl in utils.get_domain_limit_templates():
            to_create.append(
                DomainObjectLimit(domain=domain, name=name, max_value=-1))
    DomainObjectLimit.objects.bulk_create(to_create)


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0003_auto_20151118_1215'),
        ('limits', '0004_auto_20160413_1312'),
    ]

    operations = [
        migrations.RunPython(create_limits)
    ]

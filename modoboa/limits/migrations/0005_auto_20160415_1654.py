# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import modoboa.limits.models

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
        migrations.CreateModel(
            name='DomainObjectLimit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=254)),
                ('max_value', models.IntegerField(default=0)),
                ('domain', models.ForeignKey(to='admin.Domain', on_delete=models.CASCADE)),
            ],
            bases=(modoboa.limits.models.ObjectLimitMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='userobjectlimit',
            name='max_value',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterUniqueTogether(
            name='domainobjectlimit',
            unique_together=set([('domain', 'name')]),
        ),
        migrations.RunPython(create_limits)
    ]

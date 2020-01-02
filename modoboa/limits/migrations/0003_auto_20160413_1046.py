from django.db import migrations, models
from django.conf import settings


def move_limits_to_user(apps, schema_editor):
    """Move limits from Pool to User."""
    LimitsPool = apps.get_model("limits", "LimitsPool")
    UserObjectLimit = apps.get_model("limits", "UserObjectLimit")
    ContentType = apps.get_model("contenttypes", "ContentType")

    if not ContentType.objects.exists():
        # No ContentType means this is a fresh install
        return

    name_to_content_type = {
        "domains_limit": (
            ContentType.objects.get(app_label="admin", model="domain")),
        "domain_aliases_limit": (
            ContentType.objects.get(app_label="admin", model="domainalias")),
        "mailboxes_limit": (
            ContentType.objects.get(app_label="admin", model="mailbox")),
        "mailbox_aliases_limit": (
            ContentType.objects.get(app_label="admin", model="alias")),
        "domain_admins_limit": (
            ContentType.objects.get(app_label="core", model="user")),
    }

    to_create = []
    qset = (
        LimitsPool.objects.select_related("user")
        .prefetch_related("limit_set"))
    for pool in qset:
        for limit in pool.limit_set.all():
            objlimit = UserObjectLimit(
                user=pool.user, max_value=limit.maxvalue,
                name=limit.name.replace("_limit", ""),
                content_type=name_to_content_type[limit.name])
            to_create.append(objlimit)
    UserObjectLimit.objects.bulk_create(to_create)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('limits', '0002_auto_20151114_1518'),
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserObjectLimit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=254)),
                ('max_value', models.IntegerField(default=-2)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userobjectlimit',
            unique_together=set([('user', 'name')]),
        ),
        migrations.RunPython(move_limits_to_user)
    ]

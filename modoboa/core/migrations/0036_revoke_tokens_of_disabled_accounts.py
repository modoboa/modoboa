from django.db import migrations
from django.utils import timezone

from oauth2_provider.settings import oauth2_settings


def revoke_tokens(apps, schema_editor):
    """Revoke OAuth2 tokens of accounts disabled before this fix."""
    AccessToken = apps.get_model(oauth2_settings.ACCESS_TOKEN_MODEL)
    RefreshToken = apps.get_model(oauth2_settings.REFRESH_TOKEN_MODEL)
    RefreshToken.objects.filter(user__is_active=False, revoked__isnull=True).update(
        revoked=timezone.now()
    )
    AccessToken.objects.filter(user__is_active=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0035_log_object_repr"),
        migrations.swappable_dependency(oauth2_settings.ACCESS_TOKEN_MODEL),
        migrations.swappable_dependency(oauth2_settings.REFRESH_TOKEN_MODEL),
    ]

    operations = [
        migrations.RunPython(revoke_tokens, migrations.RunPython.noop),
    ]

from django.db import migrations


def remove_useless_aliases(apps, schema_editor):
    """Remove aliases linked to disabled messages."""
    ARmessage = apps.get_model("autoreply", "ARmessage")
    AliasRecipient = apps.get_model("admin", "AliasRecipient")
    qset = ARmessage.objects.select_related("mbox", "mbox__domain").filter(
        enabled=False
    )
    for armessage in qset:
        alr_address = f"{armessage.mbox.address}@{armessage.mbox.domain}@autoreply.{armessage.mbox.domain}"
        try:
            alr = AliasRecipient.objects.get(address=alr_address)
        except AliasRecipient.DoesNotExist:
            continue
        alias = alr.alias
        alr.delete()
        if not alias.recipients_count:
            alias.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("autoreply", "0004_delete_alias"),
    ]

    operations = [
        migrations.RunPython(remove_useless_aliases),
    ]

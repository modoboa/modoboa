"""Revoke the access domain admins wrongly got on privileged accounts.

When a SuperAdmin or Reseller account was created with a mailbox (or
when an account with a mailbox was promoted to one of these roles), the
administrators of the mailbox's domain were given access to the account
and to its mailbox. This let them take it over.

This data migration removes every access held on SuperAdmin and
Reseller accounts (and on their mailboxes) by accounts with a lower
role.
"""

from django.db import migrations
from django.db.models import Q


def revoke_access_on_privileged_accounts(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    User = apps.get_model("core", "User")
    ObjectAccess = apps.get_model("core", "ObjectAccess")
    Mailbox = apps.get_model("admin", "Mailbox")
    user_ct = ContentType.objects.filter(app_label="core", model="user").first()
    mailbox_ct = ContentType.objects.filter(app_label="admin", model="mailbox").first()
    if user_ct is None or mailbox_ct is None:
        # Fresh installation: no access has been granted yet.
        return
    privileged = User.objects.filter(
        Q(is_superuser=True) | Q(groups__name="Resellers")
    ).distinct()
    for account in privileged:
        targets = [(user_ct, account.pk)]
        mailbox = Mailbox.objects.filter(user=account).first()
        if mailbox is not None:
            targets.append((mailbox_ct, mailbox.pk))
        for ct, object_id in targets:
            entries = ObjectAccess.objects.filter(
                content_type=ct, object_id=object_id, user__is_superuser=False
            ).exclude(user=account)
            if not account.is_superuser:
                # Resellers keep the access they hold on other resellers.
                entries = entries.exclude(user__groups__name="Resellers")
            revoked = list(entries)
            if not revoked:
                continue
            ObjectAccess.objects.filter(pk__in=[entry.pk for entry in revoked]).delete()
            if not any(entry.is_owner for entry in revoked):
                continue
            new_owner = (
                User.objects.filter(is_superuser=True, is_active=True)
                .exclude(pk=account.pk)
                .first()
            )
            if new_owner is not None:
                ObjectAccess.objects.update_or_create(
                    user=new_owner,
                    content_type=ct,
                    object_id=object_id,
                    defaults={"is_owner": True},
                )


class Migration(migrations.Migration):
    dependencies = [
        ("admin", "0024_domain_last_dns_check_execution"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("core", "0032_objectaccess_core_object_content_6b9cf4_idx"),
    ]

    operations = [
        migrations.RunPython(
            revoke_access_on_privileged_accounts, migrations.RunPython.noop
        ),
    ]

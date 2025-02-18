"""Django signal handlers for modoboa_postfix_autoreply."""

from django.urls import re_path
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import gettext as _

from modoboa.admin import models as admin_models, signals as admin_signals
from modoboa.core import signals as core_signals
from modoboa.transport import models as tr_models

from . import forms, models


@receiver(signals.post_save, sender=admin_models.Domain)
def manage_transport_entry(sender, instance, **kwargs):
    """Create or update a transport entry for this domain."""
    if kwargs.get("created"):
        tr_models.Transport.objects.get_or_create(
            pattern=f"autoreply.{instance}", service="autoreply"
        )
        return
    oldname = getattr(instance, "oldname", "None")
    if oldname is None or oldname == instance.name:
        return
    tr_models.Transport.objects.filter(pattern=f"autoreply.{oldname}").update(
        pattern=f"autoreply.{instance.name}"
    )
    qset = admin_models.AliasRecipient.objects.select_related(
        "alias", "r_mailbox"
    ).filter(
        alias__domain=instance, alias__internal=True, address__contains="@autoreply"
    )
    for alr in qset:
        alr.address = alr.address.replace(oldname, instance.name)
        alr.save()


@receiver(signals.post_delete, sender=admin_models.Domain)
def delete_transport_entry(sender, instance, **kwargs):
    """Delete a transport entry."""
    tr_models.Transport.objects.filter(pattern=f"autoreply.{instance}").delete()


@receiver(signals.post_save, sender=admin_models.Mailbox)
def rename_autoreply_alias(sender, instance, **kwargs):
    """Rename AR alias if needed."""
    old_address = getattr(instance, "old_full_address", None)
    if old_address is None or old_address == instance.full_address:
        return
    admin_models.AliasRecipient.objects.filter(
        address__contains=f"{old_address}@autoreply"
    ).update(address=f"{instance.full_address}@autoreply.{instance.domain}")


@receiver(signals.post_delete, sender=admin_models.Mailbox)
def delete_autoreply_alias(sender, instance, **kwargs):
    """Delete alias."""
    admin_models.AliasRecipient.objects.filter(
        address=f"{instance.full_address}@autoreply.{instance.domain}"
    ).delete()


@receiver(signals.post_save, sender=models.ARmessage)
def manage_autoreply_alias(sender, instance, **kwargs):
    """Create or delete the alias."""
    ar_alias_address = f"{instance.mbox.full_address}@autoreply.{instance.mbox.domain}"
    admin_models.Alias.objects.get(
        address=instance.mbox.full_address, domain=instance.mbox.domain, internal=True
    )
    alias, created = admin_models.Alias.objects.get_or_create(
        address=instance.mbox.full_address, domain=instance.mbox.domain, internal=True
    )
    if instance.enabled:
        admin_models.AliasRecipient.objects.get_or_create(
            alias=alias, address=ar_alias_address
        )
    else:
        admin_models.AliasRecipient.objects.filter(address=ar_alias_address).delete()


@receiver(core_signals.extra_uprefs_routes)
def extra_routes(sender, **kwargs):
    """Add extra routes."""
    from . import views

    return [re_path(r"^user/autoreply/$", views.autoreply, name="autoreply")]


@receiver(core_signals.extra_static_content)
def extra_js(sender, caller, st_type, user, **kwargs):
    """Add static content."""
    if caller != "user_index" or st_type != "js":
        return ""
    return f"""function autoreply_cb() {{
    $('.datefield').datetimepicker({{
        format: 'YYYY-MM-DD HH:mm:ss',
        locale: '{user.language}'
    }});
}}
"""


@receiver(core_signals.extra_user_menu_entries)
def menu(sender, location, user, **kwargs):
    """Inject new menu entries."""
    if location != "uprefs_menu" or not hasattr(user, "mailbox"):
        return []
    return [
        {
            "name": "autoreply",
            "class": "ajaxnav",
            "url": "autoreply/",
            "label": _("Auto-reply message"),
        }
    ]


@receiver(admin_signals.extra_account_forms)
def extra_account_form(sender, user, account, **kwargs):
    """Add autoreply form to the account edition form."""
    result = []
    if user.role in ("SuperAdmins", "DomainAdmins"):
        if hasattr(account, "mailbox"):
            extraform = {
                "id": "auto_reply_message",
                "title": _("Auto reply"),
                "cls": forms.ARmessageForm,
                "new_args": [account.mailbox],
            }
            result.append(extraform)
    return result


@receiver(admin_signals.get_account_form_instances)
def fill_account_tab(sender, user, account, **kwargs):
    """Return form instance."""
    condition = user.role not in ("SuperAdmins", "DomainAdmins") or not hasattr(
        account, "mailbox"
    )
    if condition:
        return {}
    return {"auto_reply_message": account.mailbox.armessage_set.first()}

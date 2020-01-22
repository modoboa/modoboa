"""Management command to communicate with public API."""

from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from modoboa.admin import models as admin_models
from modoboa.core.extensions import exts_pool
from modoboa.lib import api_client
from ... import models
from ... import utils


class Command(BaseCommand):
    """Command class."""

    help = "Communicate with Modoboa public API."  # NOQA:A003

    def send_notification(self, local_config, extensions):
        """Send email notification about updates."""
        updates = {}
        to_create = []
        for extension in extensions:
            if "update" not in extension:
                continue
            qset = models.ExtensionUpdateHistory.objects.filter(
                extension=extension["name"], version=extension["last_version"]
            )
            if not qset.exists():
                updates[extension["name"]] = extension["last_version"]
                to_create.append(
                    models.ExtensionUpdateHistory(
                        extension=extension["name"],
                        version=extension["last_version"]
                    )
                )
        if not updates:
            return
        content = render_to_string(
            "core/notifications/update_available.html", {
                "updates": updates
            })
        subject = _("[modoboa] Update(s) available")
        sender = local_config.parameters.get_value("sender_address")
        recipient = local_config.parameters.get_value(
            "new_versions_email_rcpt")
        msg = EmailMessage(
            subject, content.strip(), sender, [recipient],
        )
        msg.send()
        models.ExtensionUpdateHistory.objects.bulk_create(to_create)

    def handle(self, *args, **options):
        """Command entry point."""
        local_config = (
            models.LocalConfig.objects.select_related("site").first())
        if not local_config.parameters.get_value("enable_api_communication"):
            return
        self.client = api_client.ModoAPIClient()
        if not local_config.api_pk:
            pk = self.client.register_instance(local_config.site.domain)
            if pk is None:
                raise CommandError("Instance registration failed.")
            local_config.api_pk = pk

        if local_config.parameters.get_value("check_new_versions"):
            versions = self.client.versions()
            if versions is None:
                raise CommandError("Failed to retrieve versions from the API.")
            local_config.api_versions = versions

        local_config.save()

        if local_config.parameters.get_value("send_new_versions_email"):
            update_avail, extensions = utils.check_for_updates()
            if update_avail:
                self.send_notification(local_config, extensions)

        if not local_config.parameters.get_value("send_statistics"):
            return
        extensions = [ext["name"] for ext in exts_pool.list_all()]
        data = {
            "hostname": local_config.site.domain,
            "known_version": self.client.local_core_version,
            "domain_counter": admin_models.Domain.objects.count(),
            "domain_alias_counter": admin_models.DomainAlias.objects.count(),
            "mailbox_counter": admin_models.Mailbox.objects.count(),
            "alias_counter": (
                admin_models.Alias.objects.filter(internal=False).count()),
            "extensions": extensions
        }
        self.client.update_instance(local_config.api_pk, data)

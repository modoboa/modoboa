"""Management command to communicate with public API."""

from django.core.management.base import BaseCommand, CommandError

from modoboa.admin import models as admin_models
from modoboa.core.extensions import exts_pool
from modoboa.lib import api_client, parameters

from ... import models


class Command(BaseCommand):
    """Command class."""

    help = "Communicate with Modoboa public API."

    def handle(self, *args, **options):
        """Command entry point."""
        if parameters.get_admin("ENABLE_API_COMMUNICATION") == "no":
            return
        self.client = api_client.ModoAPIClient()
        local_config = (
            models.LocalConfig.objects.select_related("site").first())
        if not local_config.api_pk:
            pk = self.client.register_instance(local_config.site.domain)
            if pk is None:
                raise CommandError("Instance registration failed.")
            local_config.api_pk = pk

        if parameters.get_admin("CHECK_NEW_VERSIONS") == "yes":
            versions = self.client.versions()
            if versions is None:
                raise CommandError("Failed to retrieve versions from the API.")
            local_config.api_versions = versions

        local_config.save()

        if parameters.get_admin("SEND_STATISTICS") == "no":
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
        if not self.client.update_instance(local_config.api_pk, data):
            raise CommandError("Failed to update instance.")

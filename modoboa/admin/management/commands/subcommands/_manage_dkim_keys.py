"""Management command to create DKIM keys."""

import os

from django.core.management.base import BaseCommand
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from modoboa.lib import sysutils
from modoboa.parameters import tools as param_tools

from .... import models
from ....constants import DKIM_WRITE_ERROR, ALARM_OPENED, DKIM_ERROR


class ManageDKIMKeys(BaseCommand):
    """Command class."""

    def create_new_dkim_key(self, domain):
        """Create a new DKIM key."""
        storage_dir = param_tools.get_global_parameter("dkim_keys_storage_dir")
        pkey_path = os.path.join(storage_dir, f"{domain.name}.pem")

        alarm_qset = domain.alarms.filter(internal_name=DKIM_WRITE_ERROR)
        if not os.access(storage_dir, os.W_OK):
            if not alarm_qset.exists():
                domain.alarms.create(
                    title=_(
                        "DKIM path non-writable "
                        "(either a permission issue or the directory does not exist)"
                    ),
                    internal_name=DKIM_WRITE_ERROR,
                )
            else:
                alarm = alarm_qset.first()
                if alarm.status != ALARM_OPENED:
                    alarm.reopen()
            return
        elif alarm_qset.exists():
            alarm_qset.first().close()
        key_size = (
            domain.dkim_key_length
            if domain.dkim_key_length
            else self.default_key_length
        )
        code, output = sysutils.exec_cmd(f"openssl genrsa -out {pkey_path} {key_size}")
        if code:
            print(
                f"Failed to generate DKIM private key for domain {domain.name}: {smart_str(output)}"
            )
            domain.alarms.create(
                title=_("Failed to generate DKIM private key"), internal_name=DKIM_ERROR
            )
            return
        domain.dkim_private_key_path = pkey_path
        code, output = sysutils.exec_cmd(f"openssl rsa -in {pkey_path} -pubout")
        if code:
            print(
                f"Failed to generate DKIM public key for domain {domain.name}: {smart_str(output)}"
            )
            domain.alarms.create(
                title=_("Failed to generate DKIM public key"), internal_name=DKIM_ERROR
            )
            return
        public_key = ""
        for cpt, line in enumerate(smart_str(output).splitlines()):
            if cpt == 0 or line.startswith("-----"):
                continue
            public_key += line
        domain.dkim_public_key = public_key
        domain.save(update_fields=["dkim_public_key", "dkim_private_key_path"])

    def add_arguments(self, parser):
        """Add arguments to command."""
        parser.add_argument(
            "--domain",
            type=str,
            dest="domain",
            default="",
            help="Domain target for keys generation.",
        )

    def handle(self, *args, **options):
        """Entry point."""
        self.default_key_length = param_tools.get_global_parameter(
            "dkim_default_key_length"
        )

        if options["domain"] != "":
            domain = models.Domain.objects.filter(
                name=options["domain"], enable_dkim=True, dkim_private_key_path=""
            )
            if domain.exists():
                self.create_new_dkim_key(domain[0])
            return

        qset = models.Domain.objects.filter(enable_dkim=True, dkim_private_key_path="")
        for domain in qset:
            self.create_new_dkim_key(domain)

"""Management command to create DKIM keys."""

import os

from django.core.management.base import BaseCommand
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _

from modoboa.lib import sysutils
from modoboa.parameters import tools as param_tools

from .... import models
from .... import signals
from ....constants import DKIM_WRITE_ERROR, ALARM_OPENED


class ManageDKIMKeys(BaseCommand):
    """Command class."""

    def create_new_dkim_key(self, domain):
        """Create a new DKIM key."""
        storage_dir = param_tools.get_global_parameter("dkim_keys_storage_dir")
        pkey_path = os.path.join(storage_dir, "{}.pem".format(domain.name))
        alarm_qset = domain.alarms.filter(internal_name=DKIM_WRITE_ERROR)
        if not os.access(storage_dir, os.W_OK):
            if not alarm_qset.exists():
                domain.alarms.create(
                    title=_("DKIM path non-writable"),
                    internal_name=DKIM_WRITE_ERROR)
            else:
                alarm = alarm_qset.first()
                if alarm.status != ALARM_OPENED:
                    alarm.reopen()
            return
        elif alarm_qset.exists():
            alarm_qset.first().close()
        key_size = (
            domain.dkim_key_length if domain.dkim_key_length
            else self.default_key_length)
        code, output = sysutils.exec_cmd(
            "openssl genrsa -out {} {}".format(pkey_path, key_size))
        if code:
            print("Failed to generate DKIM private key for domain {}: {}"
                  .format(domain.name, smart_text(output)))
        domain.dkim_private_key_path = pkey_path
        code, output = sysutils.exec_cmd(
            "openssl rsa -in {} -pubout".format(pkey_path))
        if code:
            print("Failed to generate DKIM public key for domain {}: {}"
                  .format(domain.name, smart_text(output)))
        public_key = ""
        for cpt, line in enumerate(smart_text(output).splitlines()):
            if cpt == 0 or line.startswith("-----"):
                continue
            public_key += line
        domain.dkim_public_key = public_key
        domain.save(update_fields=["dkim_public_key", "dkim_private_key_path"])

    def handle(self, *args, **options):
        """Entry point."""
        self.default_key_length = param_tools.get_global_parameter(
            "dkim_default_key_length")
        qset = models.Domain.objects.filter(
            enable_dkim=True, dkim_private_key_path="")
        for domain in qset:
            self.create_new_dkim_key(domain)
        if qset.exists():
            signals.new_dkim_keys.send(sender=self.__class__, domains=qset)
        signals.extra_dkim_management.send(sender=self.__class__)

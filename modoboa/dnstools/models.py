"""App related models."""

from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _

from . import constants
from . import lib


class DNSRecordManager(models.Manager):
    """Custom manager for DNSRecord."""

    def get_or_create_for_domain(self, domain, rtype, ttl=7200):
        """Get or create DNS record for given domain.

        DNS queries are not performed while `ttl` (in seconds) is still valid.
        """
        now = timezone.now()
        record = self.get_queryset().filter(
            domain=domain, type=rtype, updated__gt=now).first()
        if record:
            return record

        self.get_queryset().filter(domain=domain, type=rtype).delete()
        record = DNSRecord(domain=domain, type=rtype)
        record.get_dns_record()
        if not record.value:
            return
        record.check_syntax(ttl)
        record.save()
        return record


@python_2_unicode_compatible
class DNSRecord(models.Model):
    """A model to store DNS records for Domain."""

    domain = models.ForeignKey("admin.Domain", on_delete=models.CASCADE)
    type = models.CharField(
        max_length=15, choices=constants.DNS_RECORD_TYPES)
    value = models.TextField(blank=True)
    is_valid = models.BooleanField(default=False)
    error = models.CharField(max_length=50, null=True, blank=True)
    updated = models.DateTimeField(default=timezone.now)

    objects = DNSRecordManager()

    def __str__(self):
        return "{} ({}): {}".format(self.domain, self.type, self.value)

    def get_dns_record(self):
        """Retrieve corresponding DNS record."""
        if self.type == "dkim":
            self.value = lib.get_dkim_record(
                self.domain.name, self.domain.dkim_key_selector)
        else:
            func = getattr(lib, "get_{}_record".format(self.type))
            self.value = func(self.domain.name)

    def check_syntax(self, ttl=7200):
        """Check record syntax."""
        try:
            func = getattr(lib, "check_{}_syntax".format(self.type))
            result = func(self.value)
        except lib.DNSSyntaxError as err:
            self.error = str(err)
            self.updated = timezone.now()
            return
        except AttributeError:
            pass

        if self.type == "dkim" and result != self.domain.dkim_public_key:
            self.error = _("Public key mismatchs")
            self.updated = timezone.now()
            return

        self.error = ""
        self.is_valid = True
        self.updated = timezone.now() + datetime.timedelta(seconds=ttl)

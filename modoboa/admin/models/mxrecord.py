# -*- coding: utf-8 -*-

"""MX records storage."""

from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from modoboa.parameters import tools as param_tools


class MXRecordQuerySet(models.QuerySet):
    """Custom manager for MXRecord."""

    def has_valids(self):
        """Return managed results."""
        if param_tools.get_global_parameter("valid_mxs").strip():
            return self.filter(managed=True).exists()
        return self.exists()


class MXRecordManager(models.Manager):
    """Custom manager for MXRecord."""

    def get_or_create_for_domain(self, domain, ttl=7200):
        """Get or create MX record(s) for given domain.

        DNS queries are not performed while `ttl` (in seconds) is still valid.
        """
        from .. import lib

        now = timezone.now()
        records = self.get_queryset().filter(
            domain=domain, updated__gt=now)
        if records.exists():
            for record in records:
                yield record
            return

        self.get_queryset().filter(domain=domain).delete()

        delta = datetime.timedelta(seconds=ttl)
        domain_mxs = lib.get_domain_mx_list(domain.name)
        if len(domain_mxs) == 0:
            return
        for mx_addr, mx_ip_addr in domain_mxs:
            record = self.get_queryset().create(
                domain=domain,
                name="{}".format(mx_addr.strip(".")),
                address="{}".format(mx_ip_addr),
                updated=now + delta)
            yield record


@python_2_unicode_compatible
class MXRecord(models.Model):
    """A model used to store MX records for Domain."""

    domain = models.ForeignKey("admin.Domain", on_delete=models.CASCADE)
    name = models.CharField(max_length=254)
    address = models.GenericIPAddressField()
    managed = models.BooleanField(default=False)
    updated = models.DateTimeField()

    objects = MXRecordManager.from_queryset(MXRecordQuerySet)()

    def is_managed(self):
        if not param_tools.get_global_parameter("enable_mx_checks"):
            return False
        return bool(param_tools.get_global_parameter("valid_mxs").strip())

    def __str__(self):
        return "{0.name} ({0.address}) for {0.domain} ".format(self)


class DNSBLQuerySet(models.QuerySet):
    """Custom manager for DNSBLResultManager."""

    def blacklisted(self):
        """Return blacklisted results."""
        return self.exclude(status="")


class DNSBLResult(models.Model):
    """Store a DNSBL query result."""

    domain = models.ForeignKey("admin.Domain", on_delete=models.CASCADE)
    provider = models.CharField(max_length=254, db_index=True)
    mx = models.ForeignKey(MXRecord, on_delete=models.CASCADE)
    status = models.CharField(max_length=45, blank=True, db_index=True)

    objects = models.Manager.from_queryset(DNSBLQuerySet)()

    class Meta:
        app_label = "admin"
        unique_together = [("domain", "provider", "mx")]

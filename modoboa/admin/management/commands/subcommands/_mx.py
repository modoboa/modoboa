"""Management command to check defined domains."""

import ipaddress
from datetime import datetime
from datetime import timedelta

import dns.resolver

import gevent
from gevent import socket

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from modoboa.admin import constants
from modoboa.admin import models
from modoboa.lib import parameters
from modoboa.lib import email_utils


class CheckMXRecords(BaseCommand):
    """Command class."""

    help = "Check defined domains."

    @cached_property
    def providers(self):
        """Return a list of DNSBL providers."""
        if not hasattr(settings, "DNSBL_PROVIDERS"):
            return constants.DNSBL_PROVIDERS
        return settings.DNSBL_PROVIDERS

    @cached_property
    def sender(self):
        """Return sender address for notifications."""
        return parameters.get_admin("SENDER_ADDRESS", app="core")

    def add_arguments(self, parser):
        """Add extra arguments to command."""
        parser.add_argument(
            "--no-dnsbl", action='store_true', default=False,
            help="Skip DNSBL queries.")
        parser.add_argument(
            "--timeout", type=int, default=3,
            help="Timeout used for queries.")
        parser.add_argument(
            "--ttl", type=int, default=7200,
            help="TTL for dns query.")

    def get_mx_records_for_domain(self, domain, ttl=7200):
        try:
            answers = dns.resolver.query(domain.name, "MX")
        except dns.resolver.NoAnswer:
            return
        now = datetime.now()
        delta = timedelta(seconds=ttl)
        records = models.MXRecord.objects.filter(domain=domain,
                                                 updated__gte=now - delta)
        if records.count():
            for record in records:
                yield record
            raise StopIteration()
        models.MXRecord.objects.filter(domain=domain).delete()
        for answer in answers:
            address = None
            try:
                ipaddress.ip_address(str(answer.exchange))
            except ValueError:
                try:
                    address = socket.gethostbyname(str(answer.exchange))
                except socket.gaierror:
                    pass
            else:
                address = str(answer.exchange)
            finally:
                if address is not None:
                    record = models.MXRecord.objects.create(
                        domain=domain,
                        name=str(answer.exchange).strip('.'),
                        address=address,
                        updated=now)
                    yield record

    def query_dnsbl(self, mx_list, provider):
        """Check given IP against given provider."""
        results = {}
        for mx in mx_list:
            reverse = ".".join(reversed(mx.address.split(".")))
            pattern = "{}.{}".format(reverse, provider)
            try:
                results[mx] = socket.gethostbyname(pattern)
            except socket.gaierror:
                results[mx] = False
        return provider, results

    def store_dnsbl_result(self, domain, provider, results):
        """Store provider results for domain."""
        alerts = {}
        to_create = []
        for mx in results.keys():
            result = "" if not results[mx] else results[mx]
            dnsbl_result = models.DNSBLResult.objects.filter(
                domain=domain, provider=provider, mx=mx).first()
            if dnsbl_result is None:
                to_create.append(
                    models.DNSBLResult(
                        domain=domain, provider=provider, mx=mx,
                        status=result)
                )
            else:
                if not dnsbl_result.status and result:
                    if domain not in alerts:
                        alerts[domain] = []
                    alerts[domain].append((provider, mx))
                dnsbl_result.status = result
                dnsbl_result.save()
        models.DNSBLResult.objects.bulk_create(to_create)
        if not alerts:
            return
        content = render_to_string(
            "admin/notifications/domain_in_dnsbl.html", {
                "domain": domain, "alerts": alerts
            })
        subject = _("[modoboa] DNSBL issue(s) for domain {}").format(
            domain.name)
        for admin in domain.admins:
            if not admin.email:
                continue
            status, msg = email_utils.sendmail_simple(
                self.sender, admin.email,
                domainsubject=subject, content=content)
            if not status:
                print(msg)

    def check_domain(self, domain, timeout=3, ttl=7200, **options):
        """Check specified domain."""

        mx_list = self.get_mx_records_for_domain(domain, ttl=ttl)

        if parameters.get_admin("ENABLE_DNSBL_CHECKS") == "no":
            return
        elif options['no_dnsbl'] is True:
            return
        else:
            jobs = [
                gevent.spawn(self.query_dnsbl, mx_list, provider)
                for provider in self.providers]
            gevent.joinall(jobs, timeout)
            for job in jobs:
                if not job.successful():
                    continue
                provider, results = job.value
                self.store_dnsbl_result(domain, provider, results)

    def handle(self, *args, **options):
        """Command entry point."""
        # Remove deprecated records first
        models.DNSBLResult.objects.exclude(
            provider__in=self.providers).delete()

        for domain in models.Domain.objects.filter(enabled=True):
            self.check_domain(domain, **options)

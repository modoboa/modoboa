"""Management command to check defined domains against DNSBL providers."""

import ipaddress

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


class CheckDNSBLCommand(BaseCommand):
    """Command class."""

    help = "Check defined domains against DNSBL providers."

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
            "--timeout", type=int, default=3,
            help="Timeout used for queries.")

    def query(self, ip_list, provider):
        """Check given IP against given provider."""
        results = {}
        for ip in ip_list:
            reverse = ".".join(reversed(ip.split(".")))
            pattern = "{}.{}".format(reverse, provider)
            try:
                results[ip] = socket.gethostbyname(pattern)
            except socket.gaierror:
                results[ip] = False
        return provider, results

    def store_domain_result(self, domain, provider, results):
        """Store provider results for domain."""
        alerts = {}
        to_create = []
        for ip in results.keys():
            result = "" if not results[ip] else results[ip]
            dnsbl_result = models.DNSBLResult.objects.filter(
                domain=domain, provider=provider, mx=ip).first()
            if dnsbl_result is None:
                to_create.append(
                    models.DNSBLResult(
                        domain=domain, provider=provider, mx=ip,
                        status=result)
                )
            else:
                if not dnsbl_result.status and result:
                    if domain not in alerts:
                        alerts[domain] = []
                    alerts[domain].append((provider, ip))
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
                print msg

    def check_domain(self, domain, timeout):
        """Check specified domain."""
        resolver = dns.resolver.Resolver()
        try:
            answers = resolver.query(domain.name, "MX")
        except dns.resolver.NoAnswer:
            return
        ip_list = []
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
                    ip_list.append(address)
        if len(ip_list) == 0:
            return
        jobs = [
            gevent.spawn(self.query, ip_list, provider)
            for provider in self.providers]
        gevent.joinall(jobs, timeout)
        for job in jobs:
            if not job.successful():
                continue
            provider, results = job.value
            self.store_domain_result(domain, provider, results)

    def handle(self, *args, **options):
        """Command entry point."""
        if parameters.get_admin("ENABLE_DNSBL_CHECKS") == "no":
            return
        # Remove deprecated records first
        models.DNSBLResult.objects.exclude(
            provider__in=self.providers).delete()
        for domain in models.Domain.objects.filter(enabled=True):
            self.check_domain(domain, options.get("timeout"))

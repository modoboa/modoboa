"""Management command to check defined domains."""

from __future__ import print_function, unicode_literals

import ipaddress

import gevent
from gevent import socket

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from modoboa.admin import constants
from modoboa.admin import models
from modoboa.parameters import tools as param_tools


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
        return param_tools.get_global_parameter("sender_address", app="core")

    @cached_property
    def valid_mxs(self):
        """Return valid MXs set in admin."""
        valid_mxs = param_tools.get_global_parameter("valid_mxs")
        return [ipaddress.ip_network(u"{}".format(v.strip()))
                for v in valid_mxs.split() if v.strip()]

    def add_arguments(self, parser):
        """Add extra arguments to command."""
        parser.add_argument(
            "--no-dnsbl", action="store_true", default=False,
            help="Skip DNSBL queries.")
        parser.add_argument(
            "--email", type=str, action="append", default=[],
            help="One or more email to notify")
        parser.add_argument(
            "--skip-admin-emails", action="store_true",
            default=False,
            help="Skip domain's admins email notification.")
        parser.add_argument(
            "--domain", type=str, action="append", default=[],
            help="Domain name or id to update.")
        parser.add_argument(
            "--timeout", type=int, default=3,
            help="Timeout used for queries.")
        parser.add_argument(
            "--ttl", type=int, default=7200,
            help="TTL for dns query.")

    def query_dnsbl(self, mx_list, provider):
        """Check given IP against given DNSBL provider."""
        results = {}
        for mx in mx_list:
            reverse = ".".join(reversed(mx.address.split(".")))
            pattern = "{}.{}.".format(reverse, provider)
            try:
                results[mx] = socket.gethostbyname(pattern)
            except socket.gaierror:
                results[mx] = False
        return provider, results

    def store_dnsbl_result(self, domain, provider, results, **options):
        """Store DNSBL provider results for domain."""
        alerts = {}
        to_create = []
        for mx in results.keys():
            result = "" if not results[mx] else results[mx]
            dnsbl_result = models.DNSBLResult.objects.filter(
                domain=domain, provider=provider, mx=mx).first()
            trigger = False
            if dnsbl_result is None:
                to_create.append(
                    models.DNSBLResult(
                        domain=domain, provider=provider, mx=mx,
                        status=result)
                )
                if result:
                    trigger = True
            else:
                dnsbl_result.status = result
                dnsbl_result.save()
                if not dnsbl_result.status and result:
                    trigger = True
            if trigger:
                if domain not in alerts:
                    alerts[domain] = []
                alerts[domain].append((provider, mx))
        models.DNSBLResult.objects.bulk_create(to_create)
        if not alerts:
            return
        emails = list(options["email"])
        if not options["skip_admin_emails"]:
            emails.extend(
                domain.admins.exclude(mailbox__isnull=True)
                .values_list("email", flat=True)
            )
        if not len(emails):
            return
        with mail.get_connection() as connection:
            for domain, providers in list(alerts.items()):
                content = render_to_string(
                    "admin/notifications/domain_in_dnsbl.html", {
                        "domain": domain, "alerts": providers
                    })
                subject = _("[modoboa] DNSBL issue(s) for domain {}").format(
                    domain.name)
                msg = EmailMessage(
                    subject, content.strip(), self.sender, emails,
                    connection=connection
                )
                msg.send()

    def check_valid_mx(self, domain, mx_list, **options):
        """Check that domain's MX record exist.

        If `valid_mx` is provided, retrieved MX records must be
        contained in it.
        """
        alerts = []
        check = False
        mxs = [(mx, ipaddress.ip_address("%s" % mx.address))
               for mx in mx_list]
        valid_mxs = self.valid_mxs
        if not mxs:
            alerts.append(_("Domain {} has no MX record").format(domain))
        elif valid_mxs:
            for subnet in valid_mxs:
                for mx, addr in mxs:
                    if addr in subnet:
                        mx.managed = check = True
                        mx.save()
            if check is False:
                mx_names = [
                    "{0.name} ({0.address})".format(mx) for mx in mx_list]
                alerts.append(
                    _("MX record for domain {0} is invalid: {1}").format(
                        domain, ", ".join(mx_names))
                )
        if not alerts:
            return
        emails = list(options["email"])
        if not options["skip_admin_emails"]:
            emails.extend(
                domain.admins.exclude(mailbox__isnull=True)
                .values_list("email", flat=True)
            )
        if not len(emails):
            return
        content = render_to_string(
            "admin/notifications/domain_invalid_mx.html", {
                "domain": domain, "alerts": alerts
            })
        subject = _("[modoboa] MX issue(s) for domain {}").format(
            domain.name)
        msg = EmailMessage(subject, content.strip(), self.sender, emails)
        msg.send()

    def check_domain(self, domain, timeout=3, ttl=7200, **options):
        """Check specified domain."""
        mx_list = list(
            models.MXRecord.objects.get_or_create_for_domain(domain, ttl))

        if param_tools.get_global_parameter("enable_mx_checks"):
            self.check_valid_mx(domain, mx_list, **options)

        condition = (
            not param_tools.get_global_parameter("enable_dnsbl_checks") or
            options["no_dnsbl"] is True)
        if condition or not mx_list:
            return
        jobs = [
            gevent.spawn(self.query_dnsbl, mx_list, provider)
            for provider in self.providers]
        gevent.joinall(jobs, timeout)
        for job in jobs:
            if not job.successful():
                continue
            provider, results = job.value
            self.store_dnsbl_result(domain, provider, results, **options)

    def handle(self, *args, **options):
        """Command entry point."""
        # Remove deprecated records first
        models.DNSBLResult.objects.exclude(
            provider__in=self.providers).delete()

        if options["domain"]:
            domains = []
            for domain in options["domain"]:
                try:
                    if domain.isdigit():
                        domains.append(models.Domain.objects.get(pk=domain))
                    else:
                        domains.append(models.Domain.objects.get(name=domain))
                except models.Domain.DoesNotExist:
                    pass
        else:
            domains = models.Domain.objects.filter(
                enabled=True, enable_dns_checks=True)

        options.pop("domain")

        for domain in domains:
            if domain.uses_a_reserved_tld:
                continue
            self.check_domain(domain, **options)

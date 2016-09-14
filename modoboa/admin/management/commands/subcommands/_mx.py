"""Management command to check defined domains."""

from datetime import datetime
from datetime import timedelta
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
            "--valid-mx", type=str, action='append', default=[],
            help="Valid MX ip(s) or subnet(s) used to check that domain's MX "
                 "are your own.")
        parser.add_argument(
            "--no-dnsbl", action='store_true', default=False,
            help="Skip DNSBL queries.")
        parser.add_argument(
            "--email", type=str, action='append', default=[],
            help="One or more email to notify")
        parser.add_argument(
            "--skip-admin-emails", action='store_true',
            default=False,
            help="Skip domain's admins email notification.")
        parser.add_argument(
            "--timeout", type=int, default=3,
            help="Timeout used for queries.")
        parser.add_argument(
            "--ttl", type=int, default=7200,
            help="TTL for dns query.")

    def get_mx_records_for_domain(self, domain, ttl=7200):
        """Return one or more `models.MXRecord` for `domain`. DNS queries are
        not performed while `ttl` (in seconds) is still valid"""
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
        """Check given IP against given DNSBL provider."""
        results = {}
        for mx in mx_list:
            reverse = ".".join(reversed(mx.address.split(".")))
            pattern = "{}.{}".format(reverse, provider)
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
        emails = options['email']
        if not options['skip_admin_emails']:
            emails.extend([a.email for a in domain.admins if a.email])
        if emails:
            content = render_to_string(
                "admin/notifications/domain_in_dnsbl.html", {
                    "domain": domain, "alerts": alerts
                })
            subject = _("[modoboa] DNSBL issue(s) for domain {}").format(
                domain.name)
            for email in emails:
                status, msg = email_utils.sendmail_simple(
                    self.sender, email,
                    subject=subject, content=content)
                if not status:
                    print(msg)

    def check_valid_mx(self, domain, mx_list, valid_mx=None, **options):
        """Check that domain's MX record exist and is contains in `valid_mx` if
        the option is provided"""
        alerts = []
        check = False
        mxs = [ipaddress.ip_address(u"%s" % mx.address) for mx in mx_list]
        if valid_mx:
            for subnet in valid_mx:
                check = True in [mx in subnet for mx in mxs]
                if check is True:
                    break
        if not mxs:
            alerts.append(_("Domain {} as no MX record").format(domain))
        elif valid_mx and check is False:
            mx_names = ["{0.name} ({0.address})".format(mx) for mx in mx_list]
            args = (domain, ", ".join(mx_names))
            alerts.append(
                _("Domain {0} got an invalid MX record. Got {1}").format(*args)
            )
        if not alerts:
            return
        emails = options['email']
        if not options['skip_admin_emails']:
            emails.extend([a.email for a in domain.admins if a.email])
        if emails:
            content = render_to_string(
                "admin/notifications/domain_invalid_mx.html", {
                    "domain": domain, "valid_mx": valid_mx, "alerts": alerts
                })
            subject = _("[modoboa] MX issue(s) for domain {}").format(
                domain.name)
            for email in emails:
                status, msg = email_utils.sendmail_simple(
                    self.sender, email,
                    subject=subject, content=content)
                if not status:
                    print(msg)

    def check_domain(self, domain, timeout=3, ttl=7200, **options):
        """Check specified domain."""

        mx_list = list(self.get_mx_records_for_domain(domain, ttl=ttl))

        if parameters.get_admin("ENABLE_MX_CHECKS") != "no":
            self.check_valid_mx(domain, mx_list, **options)

        if parameters.get_admin("ENABLE_DNSBL_CHECKS") == "no":
            return
        elif options['no_dnsbl'] is True:
            return
        elif mx_list:
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
        # Check that user provide valid network addresses
        valid_mx = options['valid_mx']
        options['valid_mx'] = [ipaddress.ip_network(u"%s" % v)
                               for v in valid_mx]

        # Remove deprecated records first
        models.DNSBLResult.objects.exclude(
            provider__in=self.providers).delete()

        for domain in models.Domain.objects.filter(enabled=True):
            self.check_domain(domain, **options)

import ipaddress
import socket

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from modoboa.admin import constants, models
from modoboa.dnstools import models as dns_models
from modoboa.parameters import tools as param_tools


class DNSChecker:

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
    def config(self) -> dict:
        return dict(param_tools.get_global_parameters("admin"))

    @cached_property
    def valid_mxs(self):
        """Return valid MXs set in admin."""
        valid_mxs = self.config["valid_mxs"]
        return [
            ipaddress.ip_network(str(v.strip())) for v in valid_mxs.split() if v.strip()
        ]

    def query_dnsbl(self, mx_list, provider):
        """Check given IP against given DNSBL provider."""
        results = {}
        for ip, mxs in mx_list.items():
            try:
                ip = ipaddress.ip_address(str(ip))
            except ValueError:
                continue
            else:
                delim = "." if ip.version == 4 else ":"
                reverse = delim.join(ip.exploded.split(delim)[::-1])
            pattern = f"{reverse}.{provider}."
            try:
                result = socket.gethostbyname(pattern)
                # result from dnsbl is in ipv4 format
                splited_result = result.split(".")
                if int(splited_result[-1]) > 15:
                    # Typical dnsbl result : 127.0.0.[1-15] (depends on services)
                    result = False
            except socket.gaierror:
                result = False
            for mx in mxs:
                results[mx] = result
        return results

    def store_dnsbl_result(self, domain, provider, results):
        """Store DNSBL provider results for domain.

        Return a list of alerts.
        """
        alerts = []
        to_create = []
        for mx, result in list(results.items()):
            if not result:
                result = ""
            dnsbl_result = models.DNSBLResult.objects.filter(
                domain=domain, provider=provider, mx=mx
            ).first()
            trigger = False
            if dnsbl_result is None:
                to_create.append(
                    models.DNSBLResult(
                        domain=domain, provider=provider, mx=mx, status=result
                    )
                )
                if result:
                    trigger = True
            else:
                dnsbl_result.status = result
                dnsbl_result.save()
                if not dnsbl_result.status and result:
                    trigger = True
            alarm_name = f"domain_mx_in_dnsbl_{provider}"
            if trigger:
                title = _("MX {} listed by DNSBL provider {}").format(mx.name, provider)
                domain.alarms.create(
                    internal_name=alarm_name, status=constants.ALARM_OPENED, title=title
                )
                alerts.append((provider, mx.name))
            else:
                domain.alarms.filter(
                    internal_name=alarm_name, status=constants.ALARM_OPENED
                ).update(status=constants.ALARM_CLOSED, closed=timezone.now())
        models.DNSBLResult.objects.bulk_create(to_create)
        return alerts

    def send_alert_notifications(
        self, domain: models.Domain, alerts: list, subject: str, tpl: str
    ) -> None:
        """Send email notifications about given alerts."""
        if not self.config["enable_dns_notifications"]:
            return
        emails = domain.admins.exclude(mailbox__isnull=True).values_list(
            "email", flat=True
        )
        if not len(emails):
            return
        content = render_to_string(tpl, {"domain": domain, "alerts": alerts})
        msg = EmailMessage(subject, content.strip(), self.sender, emails)
        msg.send()

    def check_valid_mx(self, domain: models.Domain, mx_list: list) -> None:
        """
        Check that domain's MX record exist.

        If `valid_mx` is provided, retrieved MX records must be
        contained in it.
        """
        alerts = []
        check = False
        mxs = [(mx, ipaddress.ip_address(str(mx.address))) for mx in mx_list]
        valid_mxs = self.valid_mxs
        if not mxs:
            alarm, created = domain.alarms.get_or_create(
                internal_name="domain_has_no_mx",
                status=constants.ALARM_OPENED,
                defaults={"title": _("Domain has no MX record")},
            )
            if created:
                alerts.append(_("Domain {} has no MX record").format(domain.name))
        else:
            # Close opened alarm
            domain.alarms.filter(
                internal_name="domain_has_no_mx", status=constants.ALARM_OPENED
            ).update(status=constants.ALARM_CLOSED, closed=timezone.now())
            if valid_mxs:
                for subnet in valid_mxs:
                    for mx, addr in mxs:
                        if addr in subnet:
                            mx.managed = check = True
                            mx.save()
                if check is False:
                    mx_names = [f"{mx.name} ({mx.address})" for mx in mx_list]
                    alarm, created = domain.alarms.get_or_create(
                        internal_name="domain_invalid_mx",
                        status=constants.ALARM_OPENED,
                        defaults={
                            "title": _("Invalid MX record: {}").format(
                                ", ".join(mx_names)
                            )
                        },
                    )
                    if created:
                        alerts.append(
                            _("MX record for domain {0} is invalid: {1}").format(
                                domain, ", ".join(mx_names)
                            )
                        )
                else:
                    # Close opened alarm
                    domain.alarms.filter(
                        internal_name="domain_invalid_mx", status=constants.ALARM_OPENED
                    ).update(status=constants.ALARM_CLOSED, closed=timezone.now())
        if not alerts:
            return
        subject = _("[modoboa] MX issue(s) for domain {}").format(domain.name)
        tpl = "admin/notifications/domain_invalid_mx.html"
        self.send_alert_notifications(domain, alerts, subject, tpl)

    def run(self, domain: models.Domain, ttl: int = 7200):
        # Remove deprecated records first
        domain.dnsblresult_set.exclude(provider__in=self.providers).delete()

        mx_list = list(models.MXRecord.objects.get_or_create_for_domain(domain, ttl))

        if self.config["enable_mx_checks"]:
            self.check_valid_mx(domain, mx_list)

        if self.config["enable_spf_checks"]:
            dns_models.DNSRecord.objects.get_or_create_for_domain(domain, "spf", ttl)
        condition = self.config["enable_dkim_checks"] and domain.dkim_public_key
        if condition:
            dns_models.DNSRecord.objects.get_or_create_for_domain(domain, "dkim", ttl)
        if self.config["enable_dmarc_checks"]:
            dns_models.DNSRecord.objects.get_or_create_for_domain(domain, "dmarc", ttl)
        if self.config["enable_autoconfig_checks"]:
            dns_models.DNSRecord.objects.get_or_create_for_domain(
                domain, "autoconfig", ttl
            )
            dns_models.DNSRecord.objects.get_or_create_for_domain(
                domain, "autodiscover", ttl
            )

        condition = not self.config["enable_dnsbl_checks"] or not mx_list
        if condition:
            return

        mx_by_ip = {}
        for mx in mx_list:
            if mx.address not in mx_by_ip:
                mx_by_ip[mx.address] = [mx]
            elif mx not in mx_by_ip[mx.address]:
                mx_by_ip[mx.address].append(mx)

        alerts = []
        for provider in self.providers:
            results = self.query_dnsbl(mx_by_ip, provider)
            alerts += self.store_dnsbl_result(domain, provider, results)

        if not alerts:
            return

        subject = _("[modoboa] DNSBL issue(s) for domain {}").format(domain.name)
        tpl = "admin/notifications/domain_in_dnsbl.html"
        self.send_alert_notifications(domain, alerts, subject, tpl)

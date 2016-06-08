"""Management command to check defined domains against DNSBL providers."""

import ipaddress

import dns.resolver
import gevent
from gevent import socket

from django.core.management.base import BaseCommand

from modoboa.admin import constants
from modoboa.admin import models


class CheckDNSBLCommand(BaseCommand):
    """Command class."""

    help = "Check defined domains against DNSBL providers."

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

    def check_domain(self, domain, timeout):
        """Check specified domain."""
        resolver = dns.resolver.Resolver()
        answers = resolver.query(domain.name, "MX")
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

        jobs = [
            gevent.spawn(self.query, ip_list, provider)
            for provider in constants.DNSBL_PROVIDERS]
        gevent.joinall(jobs, timeout)
        for job in jobs:
            if not job.successful():
                continue
            provider, results = job.value
            for ip in results.keys():
                result = "" if not results[ip] else results[ip]
                models.DNSBLResult.objects.update_or_create(
                    domain=domain, provider=provider, mx=ip,
                    status=result)

    def handle(self, *args, **options):
        """Command entry point."""
        for domain in models.Domain.objects.filter(enabled=True):
            self.check_domain(domain, options.get("timeout"))

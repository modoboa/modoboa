"""Test utilities."""

import os
import socket

from django.conf import settings

from dns.name import Name
from dns.rdtypes.IN.A import A
from dns.rdtypes.ANY.MX import MX
from dns.rdtypes.ANY.TXT import TXT
from dns.resolver import NXDOMAIN, NoAnswer, NoNameservers, Timeout


HAVE_REDIS = "REDIS_HOST" in os.environ and "REDIS_PORT" in os.environ
try:
    import ldap
except ImportError:
    HAVE_LDAP = False
else:
    HAVE_LDAP = True


class RRset:

    def __init__(self):
        self.address = "192.0.2.1"


class RRsetInvalid:

    def __init__(self):
        self.address = "000.0.0.0"


_A_RECORD = A("IN", "A", "1.2.3.4")
_MX_RECORD_1 = MX("IN", "MX", 10, Name("mx.example.com".split(".")))
_MX_RECORD_2 = MX("IN", "MX", 10, Name("mx2.example.com".split(".")))
_MX_RECORD_3 = MX("IN", "MX", 10, Name("mx3.example.com".split(".")))
_SPF_RECORD = TXT("IN", "TXT", ["v=spf1 mx -all"])
_DMARC_RECORD = TXT("IN", "TXT", ["v=DMARC1 p=reject"])
_DKIM_RECORD = TXT("IN", "TXT", ["v=DKIM1 p=XXXXX"])
_BAD_MX_RECORD = MX("IN", "MX", 10, Name("bad-response.example.com".split(".")))
_DNE_MX_RECORD = MX("IN", "MX", 10, Name("does-not-exist.example.com".split(".")))
_MX_RECORDS = [_MX_RECORD_1]
_IP_SET_RECORDS = [RRset()]

_IPV4_RECORD_REDIS = (
    socket.AF_INET,
    socket.SOCK_STREAM,
    6,
    "",
    ("127.0.0.1", int(settings.REDIS_PORT)),
)
_IPV4_RECORD_1 = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 25))
_IPV4_RECORD_2 = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.2", 25))
_IPV6_RECORD = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 25))
_BAD_IP_RECORD = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("BAD", 25))
_IP_RECORDS = [_IPV4_RECORD_1, _IPV6_RECORD]

_POSSIBLE_DNS_RESULTS = {
    "test3.com": [_MX_RECORD_3],
    "no-mx.example.com": NoAnswer(),
    "does-not-exist.example.com": NXDOMAIN(),
    "timeout.example.com": Timeout(),
    "no-ns-servers.example.com": NoNameservers(),
    "bad-response.example.com": [_BAD_MX_RECORD],
    "no-lookup.example.com": [_DNE_MX_RECORD],
    "no-answer.example.com": [_DNE_MX_RECORD],
    "dns-checks.com": [_MX_RECORD_2],
    "invalid-mx.com": [_MX_RECORD_3],
}

_POSSIBLE_DNS_RESULTS_NO_MX = {
    "does-not-exist.example.com": NXDOMAIN(),
    "mx2.example.com": NXDOMAIN(),
    "no-lookup.example.com": NXDOMAIN(),
    "no-answer.example.com": NoAnswer(),
    "bad-response.example.com": [RRsetInvalid()],
    "dns-checks.com": [
        _SPF_RECORD,
    ],
    "modoboa._domainkey.dns-checks.com": [_DKIM_RECORD],
    "_dmarc.dns-checks.com": [
        _DMARC_RECORD,
    ],
    "autoconfig.dns-checks.com": [_A_RECORD],
    "autodiscover.dns-checks.com": [_A_RECORD],
    "mx3.example.com": [_A_RECORD],
}
_POSSIBLE_IP_RESULTS = {
    settings.REDIS_HOST: [_IPV4_RECORD_REDIS],
    "test3.com": [_IPV4_RECORD_2],
    "mx2.example.com": [_IPV4_RECORD_2],
    "bad-response.example.com": [_BAD_IP_RECORD],
    "does-not-exist.example.com": socket.gaierror(),
    "192.0.2.254": socket.gaierror(),
    "2001:db8:254": socket.gaierror(),
    "000.0.0.0": ValueError(),
}

_POSSIBLE_DNS_IPV6_RESULTS = {
    settings.REDIS_HOST: socket.getaddrinfo(settings.REDIS_HOST, settings.REDIS_PORT),
    "mx3.example.com": NoAnswer(),
}


def mock_dns_query_result(qname, *args, **kwargs):
    if "MX" in args:
        if qname in _POSSIBLE_DNS_RESULTS:
            return get_mock_dns_query_response(_POSSIBLE_DNS_RESULTS, qname)
        return _MX_RECORDS
    elif "AAAA" in args:
        if qname in _POSSIBLE_DNS_IPV6_RESULTS:
            return get_mock_dns_query_response(_POSSIBLE_DNS_IPV6_RESULTS, qname)
    if qname in _POSSIBLE_DNS_RESULTS_NO_MX:
        return get_mock_dns_query_response(_POSSIBLE_DNS_RESULTS_NO_MX, qname)
    return _IP_SET_RECORDS


def get_mock_dns_query_response(responses, attributeName):
    if isinstance(responses[attributeName], Exception):
        raise responses[attributeName]
    return responses[attributeName]


def mock_ip_address_result(host, *args, **kwargs):
    if host in _POSSIBLE_IP_RESULTS:
        if isinstance(_POSSIBLE_IP_RESULTS[host], Exception):
            raise _POSSIBLE_IP_RESULTS[host]
        else:
            return _POSSIBLE_IP_RESULTS[host]
    return _IP_RECORDS


def mock_ip_query_result(host, port, *args, **kwargs):
    if host in _POSSIBLE_IP_RESULTS:
        if isinstance(_POSSIBLE_IP_RESULTS[host], Exception):
            raise _POSSIBLE_IP_RESULTS[host]
        else:
            return _POSSIBLE_IP_RESULTS[host]
    return _IP_RECORDS

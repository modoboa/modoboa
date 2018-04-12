# -*- coding: utf-8 -*-

"""Test utilities."""

from __future__ import unicode_literals

import socket

from dns.name import Name
from dns.rdtypes.ANY.MX import MX
from dns.resolver import NXDOMAIN, NoAnswer, NoNameservers, Timeout

_MX_RECORD_1 = MX("IN", "MX", 10, Name("mx.example.com".split(".")))
_MX_RECORD_2 = MX("IN", "MX", 10, Name("mx2.example.com".split(".")))
_BAD_MX_RECORD = MX("IN", "MX", 10, Name("bad-response.example.com".split(".")))
_DNE_MX_RECORD = MX("IN", "MX", 10, Name(
    "does-not-exist.example.com".split(".")))
_MX_RECORDS = [_MX_RECORD_1]

_IPV4_RECORD_1 = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 25))
_IPV4_RECORD_2 = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.2", 25))
_IPV6_RECORD = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 25))
_BAD_IP_RECORD = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("BAD", 25))
_IP_RECORDS = [_IPV4_RECORD_1, _IPV6_RECORD]

_POSSIBLE_DNS_RESULTS = {
    "test3.com": [_MX_RECORD_2],
    "no-mx.example.com": NoAnswer(),
    "does-not-exist.example.com": NXDOMAIN(),
    "timeout.example.com": Timeout(),
    "no-ns-servers.example.com": NoNameservers(),
    "bad-response.example.com": [_BAD_MX_RECORD],
    "no-lookup.example.com": [_DNE_MX_RECORD],
}

_POSSIBLE_IP_RESULTS = {
    "test3.com": [_IPV4_RECORD_2],
    "mx2.example.com": [_IPV4_RECORD_2],
    "bad-response.example.com": [_BAD_IP_RECORD],
    "does-not-exist.example.com": socket.gaierror(),
    "192.0.2.254": socket.gaierror(),
    "2001:db8:254": socket.gaierror(),
}


def mock_dns_query_result(qname, *args, **kwargs):
    if qname in _POSSIBLE_DNS_RESULTS:
        if isinstance(_POSSIBLE_DNS_RESULTS[qname], Exception):
            raise _POSSIBLE_DNS_RESULTS[qname]
        else:
            return _POSSIBLE_DNS_RESULTS[qname]

    return _MX_RECORDS


def mock_ip_query_result(host, port, *args, **kwargs):
    if host in _POSSIBLE_IP_RESULTS:
        if isinstance(_POSSIBLE_IP_RESULTS[host], Exception):
            raise _POSSIBLE_IP_RESULTS[host]
        else:
            return _POSSIBLE_IP_RESULTS[host]

    return _IP_RECORDS

# -*- coding: utf-8 -*-

"""Admin constants."""

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

DNSBL_PROVIDERS = [
    "aspews.ext.sorbs.net",
    "b.barracudacentral.org",
    "bad.psky.me",
    "bl.deadbeef.com",
    "bl.emailbasura.org",
    "bl.spamcop.net",
    "blackholes.five-ten-sg.com",
    "blacklist.woody.ch",
    "bogons.cymru.com",
    "cbl.abuseat.org",
    "cdl.anti-spam.org.cn",
    "combined.abuse.ch",
    "combined.rbl.msrbl.net",
    "db.wpbl.info",
    "dnsbl-1.uceprotect.net",
    "dnsbl-2.uceprotect.net",
    "dnsbl-3.uceprotect.net",
    "dnsbl.inps.de",
    "dnsbl.sorbs.net",
    "drone.abuse.ch",
    "duinv.aupads.org",
    "dul.dnsbl.sorbs.net",
    "dul.ru",
    "dyna.spamrats.com",
    "dynip.rothen.com",
    "http.dnsbl.sorbs.net"
    "images.rbl.msrbl.net",
    "ips.backscatterer.org",
    "ix.dnsbl.manitu.net",
    "korea.services.net",
    "misc.dnsbl.sorbs.net",
    "noptr.spamrats.com",
    "ohps.dnsbl.net.au",
    "omrs.dnsbl.net.au",
    "orvedb.aupads.org",
    "osps.dnsbl.net.au",
    "osrs.dnsbl.net.au",
    "owfs.dnsbl.net.au",
    "owps.dnsbl.net.au"
    "pbl.spamhaus.org",
    "phishing.rbl.msrbl.net",
    "probes.dnsbl.net.au"
    "proxy.bl.gweep.ca",
    "proxy.block.transip.nl",
    "psbl.surriel.com",
    "rbl.interserver.net",
    "rdts.dnsbl.net.au",
    "relays.bl.gweep.ca",
    "relays.bl.kundenserver.de",
    "relays.nether.net",
    "residential.block.transip.nl",
    "ricn.dnsbl.net.au",
    "rmst.dnsbl.net.au",
    "sbl.spamhaus.org",
    "short.rbl.jp",
    "smtp.dnsbl.sorbs.net",
    "socks.dnsbl.sorbs.net",
    "spam.abuse.ch",
    "spam.dnsbl.sorbs.net",
    "spam.rbl.msrbl.net",
    "spam.spamrats.com",
    "spamlist.or.kr",
    "spamrbl.imp.ch",
    "t3direct.dnsbl.net.au",
    "ubl.lashback.com",
    "ubl.unsubscore.com",
    "virbl.bit.nl",
    "virus.rbl.jp",
    "virus.rbl.msrbl.net",
    "web.dnsbl.sorbs.net",
    "wormrbl.imp.ch",
    "xbl.spamhaus.org",
    "zen.spamhaus.org",
    "zombie.dnsbl.sorbs.net",
]

# Do not run tests for these domains.
# https://en.wikipedia.org/wiki/Top-level_domain#Reserved_domains
RESERVED_TLD = [
    "example",
    "invalid",
    "localhost",
    "test"
]

DOMAIN_TYPES = [
    ("domain", _("Domain")),
    ("relaydomain", _("Relay domain")),
]

DKIM_KEY_LENGTHS = [
    (1024, "1024"),
    (2048, "2048"),
    (4096, "4096"),
]

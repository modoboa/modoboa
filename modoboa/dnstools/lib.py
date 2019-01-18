"""dnstools library."""

from __future__ import unicode_literals

import ipaddress

from django.utils.translation import ugettext as _

from modoboa.admin import lib as admin_lib

from . import constants


def get_spf_record(domain):
    """Return SPF record for domain (if any)."""
    records = admin_lib.get_dns_records(domain, "TXT")
    if records is None:
        return None
    for record in records:
        value = str(record).strip('"')
        if value.startswith("v=spf1"):
            return value
    return None


def get_dkim_record(domain, selector):
    """Return DKIM records form domain (if any)."""
    name = "{}._domainkey.{}".format(selector, domain)
    records = admin_lib.get_dns_records(name, "TXT")
    if records is None:
        return None
    for record in records:
        value = str(record).strip('"')
        if value.startswith("v=DKIM1"):
            return value
    return None


def get_dmarc_record(domain):
    """Return DMARC record for domain (if any)."""
    name = "_dmarc.{}".format(domain)
    records = admin_lib.get_dns_records(name, "TXT")
    if records is None:
        return None
    for record in records:
        value = str(record).strip('"')
        if value.startswith("v=DMARC1"):
            return value
    return None


def _get_simple_record(name):
    """We just want to know if name is declared."""
    for rdtype in ["A", "CNAME", "AAAA"]:
        records = admin_lib.get_dns_records(name, rdtype)
        if records is not None:
            break
    else:
        return None
    for record in records:
        value = str(record).strip('"')
        break
    return value


def get_autoconfig_record(domain):
    """Return autoconfig record for domain (if any)."""
    return _get_simple_record("autoconfig.{}".format(domain))


def get_autodiscover_record(domain):
    """Return autodiscover record for domain (if any)."""
    return _get_simple_record("autodiscover.{}".format(domain))


class DNSSyntaxError(Exception):
    """Custom exception for DNS errors."""

    pass


def check_spf_ip4(value):
    """Check syntax of ip4 mechanism."""
    parts = value.split(":")
    if len(parts) != 2:
        raise DNSSyntaxError(_("Wrong ip4 mechanism syntax"))
    try:
        ipaddress.ip_network(parts[1], False)
    except ValueError:
        raise DNSSyntaxError(_("Wrong IPv4 address format"))


def check_spf_ip6(value):
    """Check syntax of ip6 mechanism."""
    if not value.startswith("ip6:"):
        raise DNSSyntaxError(_("Wrong ip6 mechanism syntax"))
    value = value.replace("ip6:", "")
    try:
        ipaddress.ip_network(value, False)
    except ValueError:
        raise DNSSyntaxError(_("Wrong IPv6 address format"))


def _check_domain_and_mask(value, mechanism):
    """Check for valid domain / mask."""
    domain = None
    mask = None
    if ":" in value:
        mechanism, domain = value.split(":")
        if "/" in domain:
            domain, mask = domain.split("/")
    elif "/" in value:
        mechanism, mask = value.split("/")
    else:
        raise DNSSyntaxError(
            _("Invalid syntax for {} mechanism").format(mechanism))
    if mask and (not mask.isdigit() or int(mask) > 32):
        raise DNSSyntaxError(_("Invalid mask found {}").format(mask))


def check_spf_a(value):
    """Check syntax of a mechanism."""
    if value == "a":
        return
    _check_domain_and_mask(value, "a")


def check_spf_mx(value):
    """Check syntax of mx mechanism."""
    if value == "mx":
        return
    _check_domain_and_mask(value, "mx")


def _check_simple(value, mechanism):
    """Simple check."""
    if value == mechanism:
        return
    parts = value.split(":")
    if len(parts) != 2:
        raise DNSSyntaxError(
            _("Invalid syntax for {} mechanism").format(mechanism))


def check_spf_ptr(value):
    """Check syntax of ptr mechanism."""
    _check_simple(value, "ptr")


def check_spf_exists(value):
    """Check syntax of ptr mechanism."""
    _check_simple(value, "exists")


def check_spf_include(value):
    """Check syntax of include mechanism."""
    _check_simple(value, "include")


def check_spf_syntax(record):
    """Check if record has a valid SPF syntax."""
    if not record.startswith("v=spf1"):
        raise DNSSyntaxError(_("Not an SPF record"))
    parts = record.split(" ")[1:]
    modifiers = []
    mechanisms = []
    for part in parts:
        if part == "":
            continue
        qualifier = None
        if part[0] in ["+", "-", "~", "?"]:
            qualifier = part[0]
            part = part[1:]
        if part == "all":
            continue
        for mechanism in constants.SPF_MECHANISMS:
            if part.startswith(mechanism):
                globals()["check_spf_{}".format(mechanism)](part)
                mechanisms.append(mechanism)
                break
        else:
            # Look for modifier
            modifier = part.split("=")
            if len(modifier) != 2:
                raise DNSSyntaxError(_("Unknown mechanism {}").format(part))
            if modifier[0] not in ["redirect", "exp"]:
                raise DNSSyntaxError(_("Unknown modifier {}").format(
                    modifier[0]))
            if modifier[0] in modifiers:
                raise DNSSyntaxError(_("Duplicate modifier {} found").format(
                    modifier[0]))
            modifiers.append(modifier[0])
    if not len(mechanisms) and not len(modifiers):
        raise DNSSyntaxError(_("No mechanism found"))
    return None


def check_dkim_syntax(record):
    """Check if record has a valid DKIM syntax."""
    if not record.startswith("v=DKIM1"):
        raise DNSSyntaxError(_("Not a valid DKIM record"))
    key = None
    for tag in record.split(";")[1:]:
        tag = tag.strip(" ")
        if tag == "":
            continue
        parts = tag.split("=", 1)
        if len(parts) != 2:
            raise DNSSyntaxError(_("Invalid tag {}").format(tag))
        name = parts[0].strip(" ")
        if name == "p":
            key = "".join(part.strip('"') for part in parts[1].split(" "))
    if key is None:
        raise DNSSyntaxError(_("No key found in record"))
    return key


def check_dmarc_tag_string_value(tag, value):
    """Check if value is valid for tag."""
    tdef = constants.DMARC_TAGS[tag]
    error = _("Wrong value {} for tag {}").format(value, tag)
    if "values" in tdef and value not in tdef["values"]:
        raise DNSSyntaxError(error)
    elif "regex" in tdef and tdef["regex"].match(value) is None:
        raise DNSSyntaxError(error)


def check_dmarc_tag(tag, value):
    """Check if tag is valid."""
    tdef = constants.DMARC_TAGS[tag]
    ttype = tdef.get("type", "string")
    if ttype == "list":
        for svalue in value.split(","):
            check_dmarc_tag_string_value(tag, svalue)
    elif ttype == "int":
        error = _("Wrong value {} for tag {}:").format(value, tag)
        try:
            value = int(value)
        except ValueError:
            raise DNSSyntaxError(error + _(" not an integer"))
        if "min_value" in tdef and value < tdef["min_value"]:
            raise DNSSyntaxError(
                error + _(" less than {}").format(tdef["min_value"]))
        if "max_value" in tdef and value > tdef["max_value"]:
            raise DNSSyntaxError(
                error + _(" greater than {}").format(tdef["max_value"]))
    else:
        check_dmarc_tag_string_value(tag, value)


def check_dmarc_syntax(record):
    """Check if record has a valid DMARC syntax."""
    if not record.startswith("v=DMARC1"):
        raise DNSSyntaxError(_("Not a valid DMARC record"))
    tags = {}
    for tag in record.split(";")[1:]:
        if tag == "":
            continue
        tag = tag.strip(" ")
        parts = tag.split("=")
        if len(parts) != 2:
            raise DNSSyntaxError(_("Invalid tag {}").format(tag))
        name = parts[0].strip(" ")
        if name not in constants.DMARC_TAGS:
            raise DNSSyntaxError(_("Unknown tag {}").format(name))
        value = parts[1].strip(" ")
        check_dmarc_tag(name, value)
        tags[name] = value
    if "p" not in tags:
        raise DNSSyntaxError(_("Missing required p tag"))

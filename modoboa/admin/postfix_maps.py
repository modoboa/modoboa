# -*- coding: utf-8 -*-

"""Map file definitions for postfix."""

from __future__ import unicode_literals


class DomainsMap(object):

    """Map to list all domains."""

    filename = "sql-domains.cf"
    mysql = (
        "SELECT name FROM admin_domain "
        "WHERE name='%s' AND type='domain' AND enabled=1"
    )
    postgres = (
        "SELECT name FROM admin_domain "
        "WHERE name='%s' AND type='domain' AND enabled"
    )
    sqlite = (
        "SELECT name FROM admin_domain "
        "WHERE name='%s' AND type='domain' AND enabled=1"
    )


class DomainsAliasesMap(object):

    """Map to list all domain aliases."""

    filename = "sql-domain-aliases.cf"
    mysql = (
        "SELECT dom.name FROM admin_domain dom "
        "INNER JOIN admin_domainalias domal ON dom.id=domal.target_id "
        "WHERE domal.name='%s' AND domal.enabled=1 AND dom.enabled=1"
    )
    postgres = (
        "SELECT dom.name FROM admin_domain dom "
        "INNER JOIN admin_domainalias domal ON dom.id=domal.target_id "
        "WHERE domal.name='%s' AND domal.enabled AND dom.enabled"
    )
    sqlite = (
        "SELECT dom.name FROM admin_domain dom "
        "INNER JOIN admin_domainalias domal ON dom.id=domal.target_id "
        "WHERE domal.name='%s' AND domal.enabled=1 AND dom.enabled=1"
    )


class AliasesMap(object):

    """A map to list all mailbox aliases."""

    filename = "sql-aliases.cf"
    mysql = (
        "SELECT alr.address FROM modoboa_admin_aliasrecipient AS alr "
        "INNER JOIN admin_alias AS al ON alr.alias_id=al.id "
        "WHERE al.enabled=1 AND al.address='%s' AND "
        "(al.expire_at IS NULL OR al.expire_at>now())"
    )
    postgres = (
        "SELECT alr.address FROM modoboa_admin_aliasrecipient AS alr "
        "INNER JOIN admin_alias AS al ON alr.alias_id=al.id "
        "WHERE al.enabled AND al.address='%s' AND "
        "(al.expire_at IS NULL OR al.expire_at>now())"
    )
    sqlite = (
        "SELECT alr.address FROM modoboa_admin_aliasrecipient AS alr "
        "INNER JOIN admin_alias AS al ON alr.alias_id=al.id "
        "WHERE al.enabled=1 AND al.address='%s' AND "
        "(al.expire_at IS NULL OR al.expire_at>datetime('now'))"
    )


class MaintainMap(object):

    """Map files to list non available mailboxes."""

    filename = "sql-maintain.cf"
    mysql = (
        "SELECT '450 Requested mail action not taken: mailbox unavailable' "
        "FROM admin_mailbox mb INNER JOIN admin_domain dom "
        "ON mb.domain_id=dom.id INNER JOIN admin_mailboxoperation mbop "
        "ON mbop.mailbox_id=mb.id WHERE dom.name='%d' AND mb.address='%u' "
        "LIMIT 1"
    )
    postgres = (
        "SELECT '450 Requested mail action not taken: mailbox unavailable' "
        "FROM admin_mailbox mb INNER JOIN admin_domain dom "
        "ON mb.domain_id=dom.id INNER JOIN admin_mailboxoperation mbop "
        "ON mbop.mailbox_id=mb.id WHERE dom.name='%d' AND mb.address='%u' "
        "LIMIT 1"
    )
    sqlite = (
        "SELECT '450 Requested mail action not taken: mailbox unavailable' "
        "FROM admin_mailbox mb INNER JOIN admin_domain dom "
        "ON mb.domain_id=dom.id INNER JOIN admin_mailboxoperation mbop "
        "ON mbop.mailbox_id=mb.id WHERE dom.name='%d' AND mb.address='%u' "
        "LIMIT 1"
    )


class SenderLoginMap(object):
    """Map file to list authorized sender addresses for a given account:
    * Its mailbox
    * Its aliases
    * Extra addresses
    """

    filename = "sql-sender-login-map.cf"
    mysql = (
        "(SELECT email FROM core_user WHERE email='%s' AND is_active=1) "
        "UNION "
        "(SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb "
        "INNER JOIN admin_senderaddress sad ON sad.mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "WHERE sad.address='%s') "
        "UNION "
        "(SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb "
        "INNER JOIN modoboa_admin_aliasrecipient alr ON alr.r_mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "INNER JOIN admin_alias al ON alr.alias_id=al.id "
        "LEFT JOIN admin_domainalias adoma ON adoma.target_id=al.domain_id "
        "LEFT JOIN admin_domain adom ON adom.id=adoma.target_id "
        "WHERE al.enabled=1 AND ("
        "  al.address='%s' OR ("
        "    adoma.name='%d' AND al.address=concat('%u', '@', adom.name)"
        ")))"
    )
    postgres = (
        "(SELECT email FROM core_user WHERE email='%s' AND is_active) "
        "UNION "
        "(SELECT mb.address || '@' || dom.name FROM admin_mailbox mb "
        "INNER JOIN admin_senderaddress sad ON sad.mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "WHERE sad.address='%s') "
        "UNION "
        "(SELECT mb.address || '@' || dom.name FROM admin_mailbox mb "
        "INNER JOIN modoboa_admin_aliasrecipient alr ON alr.r_mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "INNER JOIN admin_alias al ON alr.alias_id=al.id "
        "LEFT JOIN admin_domainalias adoma ON adoma.target_id=al.domain_id "
        "LEFT JOIN admin_domain adom ON adom.id=adoma.target_id "
        "WHERE al.enabled AND ("
        "  al.address='%s' OR ("
        "    adoma.name='%d' AND al.address='%u'||'@'||adom.name"
        ")))"
    )
    sqlite = (
        "SELECT email FROM core_user WHERE email='%s' AND is_active=1 "
        "UNION "
        "SELECT mb.address || '@' || dom.name FROM admin_mailbox mb "
        "INNER JOIN admin_senderaddress sad ON sad.mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "WHERE sad.address='%s' "
        "UNION "
        "SELECT mb.address || '@' || dom.name FROM admin_mailbox mb "
        "INNER JOIN modoboa_admin_aliasrecipient alr ON alr.r_mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "INNER JOIN admin_alias al ON alr.alias_id=al.id "
        "LEFT JOIN admin_domainalias adoma ON adoma.target_id=al.domain_id "
        "LEFT JOIN admin_domain adom ON adom.id=adoma.target_id "
        "WHERE al.enabled=1 AND ("
        "  al.address='%s' OR ("
        "    adoma.name='%d' AND al.address='%u'||'@'||adom.name"
        "))"
    )

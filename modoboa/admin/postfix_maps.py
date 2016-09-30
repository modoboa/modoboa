"""Map file definitions for postfix."""


class DomainsMap(object):

    """Map to list all domains."""

    filename = 'sql-domains.cf'
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

    filename = 'sql-domain-aliases.cf'
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

    filename = 'sql-aliases.cf'
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
        "(al.expire_at IS NULL OR al.expire_at>now())"
    )


class MaintainMap(object):

    """Map files to list non available mailboxes."""

    filename = 'sql-maintain.cf'
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


class SenderLoginMailboxMap(object):

    """Map file to list authorized sender addresses (from mailboxes)."""

    filename = "sql-sender-login-mailboxes.cf"
    mysql = (
        "SELECT email FROM core_user WHERE email='%s' AND is_active=1 "
    )
    postgres = (
        "SELECT email FROM core_user WHERE email='%s' AND is_active"
    )
    sqlite = (
        "SELECT email FROM core_user WHERE email='%s' AND is_active=1"
    )


class SenderLoginMailboxExtraMap(object):
    """Map file to list per-mailbox extra addresses."""

    filename = "sql-sender-login-mailboxes-extra.cf"

    # FIXME: is it necessary to filter against user status?

    mysql = (
        "SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb "
        "INNER JOIN admin_senderaddress sad ON sad.mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "WHERE sad.address='%s'"
    )
    postgres = (
        "SELECT mb.address || '@' || dom.name) FROM admin_mailbox mb "
        "INNER JOIN admin_senderaddress sad ON sad.mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "WHERE sad.address='%s'"
    )
    sqlite = (
        "SELECT mb.address || '@' || dom.name) FROM admin_mailbox mb "
        "INNER JOIN admin_senderaddress sad ON sad.mailbox_id=mb.id "
        "INNER JOIN admin_domain dom ON dom.id=mb.domain_id "
        "WHERE sad.address='%s'"
    )


class SenderLoginAliasMap(object):

    """Map file to list authorized sender addresses (from aliases)."""

    filename = "sql-sender-login-aliases.cf"
    mysql = (
        "SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb "
        "INNER JOIN modoboa_admin_aliasrecipient alr ON alr.r_mailbox_id=mb.id"
        " INNER JOIN admin_domain dom ON dom.id=mb.domain_id"
        " INNER JOIN admin_alias al ON alr.alias_id=al.id "
        "WHERE al.enabled=1 AND al.address='%s'"
    )
    postgres = (
        "SELECT mb.address || '@' || dom.name FROM admin_mailbox mb "
        "INNER JOIN modoboa_admin_aliasrecipient alr ON alr.r_mailbox_id=mb.id"
        " INNER JOIN admin_domain dom ON dom.id=mb.domain_id"
        " INNER JOIN admin_alias al ON alr.alias_id=al.id "
        "WHERE al.enabled AND al.address='%s'"
    )
    sqlite = (
        "SELECT mb.address || '@' || dom.name FROM admin_mailbox mb "
        "INNER JOIN modoboa_admin_aliasrecipient alr ON alr.r_mailbox_id=mb.id"
        " INNER JOIN admin_domain dom ON dom.id=mb.domain_id"
        " INNER JOIN admin_alias al ON alr.alias_id=al.id "
        "WHERE al.enabled=1 AND al.address='%s'"
    )

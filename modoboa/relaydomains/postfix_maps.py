"""Map file definitions for postfix."""


class RelayDomainsMap(object):

    """Map file to list all relay domains."""

    filename = "sql-relaydomains.cf"
    mysql = (
        "SELECT name FROM admin_domain "
        "WHERE name='%s' AND type='relaydomain' AND enabled=1"
    )
    postgres = (
        "SELECT name FROM admin_domain "
        "WHERE name='%s' AND type='relaydomain' AND enabled"
    )
    sqlite = (
        "SELECT name FROM admin_domain "
        "WHERE name='%s' AND type='relaydomain' AND enabled=1"
    )


class RelayDomainsTransportMap(object):

    """A transport map for relay domains."""

    filename = "sql-relaydomains-transport.cf"
    mysql = (
        "SELECT CONCAT(srv.name, ':[', rdom.target_host, ']') "
        "FROM postfix_relay_domains_service AS srv "
        "INNER JOIN postfix_relay_domains_relaydomain AS rdom "
        "ON rdom.service_id=srv.id "
        "INNER JOIN admin_domain AS dom ON rdom.domain_id=dom.id "
        "WHERE dom.enabled=1 AND dom.name='%s'"
    )
    postgres = (
        "SELECT srv.name || ':[' || rdom.target_host || ']' "
        "FROM postfix_relay_domains_service AS srv "
        "INNER JOIN postfix_relay_domains_relaydomain AS rdom "
        "ON rdom.service_id=srv.id "
        "INNER JOIN admin_domain AS dom ON rdom.domain_id=dom.id "
        "WHERE dom.enabled AND dom.name='%s'"
    )
    sqlite = (
        "SELECT srv.name || ':[' || rdom.target_host || ']' "
        "FROM postfix_relay_domains_service AS srv "
        "INNER JOIN postfix_relay_domains_relaydomain AS rdom "
        "ON rdom.service_id=srv.id "
        "INNER JOIN admin_domain AS dom ON rdom.domain_id=dom.id "
        "WHERE dom.enabled=1 AND dom.name='%s'"
    )


class SplitedDomainsTransportMap(object):

    """A transport map for splited domains.

    (ie. ones with both local and remote mailboxes)
    """

    filename = "sql-spliteddomains-transport.cf"
    mysql = (
        "SELECT 'lmtp:unix:private/dovecot-lmtp' "
        "FROM postfix_relay_domains_relaydomain AS rdom "
        "INNER JOIN admin_domain AS dom "
        "ON rdom.domain_id=dom.id "
        "INNER JOIN admin_mailbox AS mbox ON dom.id=mbox.domain_id "
        "INNER JOIN core_user AS u ON mbox.user_id=u.id "
        "WHERE dom.enabled=1 AND dom.name='%d' AND u.is_active=1 "
        "AND mbox.address='%u'"
    )
    postgres = (
        "SELECT 'lmtp:unix:private/dovecot-lmtp' "
        "FROM postfix_relay_domains_relaydomain AS rdom "
        "INNER JOIN admin_domain AS dom "
        "ON rdom.domain_id=dom.id "
        "INNER JOIN admin_mailbox AS mbox ON dom.id=mbox.domain_id "
        "INNER JOIN core_user AS u ON mbox.user_id=u.id "
        "WHERE dom.enabled AND dom.name='%d' AND u.is_active "
        "AND mbox.address='%u'"
    )
    sqlite = (
        "SELECT 'lmtp:unix:private/dovecot-lmtp' "
        "FROM postfix_relay_domains_relaydomain AS rdom "
        "INNER JOIN admin_domain AS dom "
        "ON rdom.domain_id=dom.id "
        "INNER JOIN admin_mailbox AS mbox ON dom.id=mbox.domain_id "
        "INNER JOIN core_user AS u ON mbox.user_id=u.id "
        "WHERE dom.enabled=1 AND dom.name='%d' AND u.is_active=1 "
        "AND mbox.address='%u'"
    )


class RelayRecipientVerification(object):

    """A map file to enable recipient verification."""

    filename = "sql-relay-recipient-verification.cf"
    mysql = (
        "SELECT 'reject_unverified_recipient' "
        "FROM postfix_relay_domains_relaydomain AS rdom "
        "INNER JOIN admin_domain AS dom ON rdom.domain_id=dom.id "
        "WHERE rdom.verify_recipients=1 AND dom.name='%d'"
    )
    postgres = (
        "SELECT 'reject_unverified_recipient' "
        "FROM postfix_relay_domains_relaydomain AS rdom "
        "INNER JOIN admin_domain AS dom ON rdom.domain_id=dom.id "
        "WHERE rdom.verify_recipients AND dom.name='%d'"
    )
    sqlite = (
        "SELECT 'reject_unverified_recipient' "
        "FROM postfix_relay_domains_relaydomain AS rdom "
        "INNER JOIN admin_domain AS dom ON rdom.domain_id=dom.id "
        "WHERE rdom.verify_recipients=1 AND dom.name='%d'"
    )

# -*- coding: utf-8 -*-

"""Map file definitions for postfix."""

from __future__ import unicode_literals


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


class SplitedDomainsTransportMap(object):

    """A transport map for splited domains.

    (ie. ones with both local and remote mailboxes)
    """

    filename = "sql-spliteddomains-transport.cf"
    mysql = (
        "SELECT 'lmtp:unix:private/dovecot-lmtp' "
        "FROM admin_domain AS dom "
        "INNER JOIN admin_mailbox AS mbox ON dom.id=mbox.domain_id "
        "INNER JOIN core_user AS u ON mbox.user_id=u.id "
        "WHERE dom.type='relaydomain' AND dom.enabled=1 "
        "AND dom.name='%d' AND u.is_active=1 "
        "AND mbox.address='%u'"
    )
    postgres = (
        "SELECT 'lmtp:unix:private/dovecot-lmtp' "
        "FROM admin_domain AS dom "
        "INNER JOIN admin_mailbox AS mbox ON dom.id=mbox.domain_id "
        "INNER JOIN core_user AS u ON mbox.user_id=u.id "
        "WHERE dom.type='relaydomain' AND dom.enabled "
        "AND dom.name='%d' AND u.is_active "
        "AND mbox.address='%u'"
    )
    sqlite = (
        "SELECT 'lmtp:unix:private/dovecot-lmtp' "
        "FROM admin_domain AS dom "
        "INNER JOIN admin_mailbox AS mbox ON dom.id=mbox.domain_id "
        "INNER JOIN core_user AS u ON mbox.user_id=u.id "
        "WHERE dom.type='relaydomain' AND dom.enabled=1 "
        "AND dom.name='%d' AND u.is_active=1 "
        "AND mbox.address='%u'"
    )


class RelayRecipientVerification(object):

    """A map file to enable recipient verification."""

    filename = "sql-relay-recipient-verification.cf"
    mysql = (
        "SELECT action FROM relaydomains_recipientaccess WHERE pattern='%d'"
    )
    postgres = (
        "SELECT action FROM relaydomains_recipientaccess WHERE pattern='%d'"
    )
    sqlite = (
        "SELECT action FROM relaydomains_recipientaccess WHERE pattern='%d'"
    )

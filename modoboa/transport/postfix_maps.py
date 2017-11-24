"""Map file definitions for postfix."""

from __future__ import unicode_literals


class TransportMap(object):
    """A transport map."""

    filename = "sql-transport.cf"
    mysql = (
        "SELECT CONCAT(service, ':', next_hop) "
        "FROM transport_transport "
        "WHERE enabled=1 AND pattern='%s'"
    )
    postgres = (
        "SELECT service || ':' || next_hop "
        "FROM transport_transport "
        "WHERE enabled AND pattern='%s'"
    )
    sqlite = (
        "SELECT service || ':' || next_hop "
        "FROM transport_transport "
        "WHERE enabled=1 AND pattern='%s'"
    )

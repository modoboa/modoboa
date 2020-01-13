"""Map file definitions for postfix."""

class TransportMap(object):
    """A transport map."""

    filename = "sql-transport.cf"
    mysql = (
        "SELECT CONCAT(service, ':', next_hop) "
        "FROM transport_transport "
        "WHERE pattern='%s'"
    )
    postgres = (
        "SELECT service || ':' || next_hop "
        "FROM transport_transport "
        "WHERE pattern='%s'"
    )
    sqlite = (
        "SELECT service || ':' || next_hop "
        "FROM transport_transport "
        "WHERE pattern='%s'"
    )

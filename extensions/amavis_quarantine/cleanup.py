#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mailng.lib import db
from mailng.conf import settings

if __name__ == "__main__":
    conn = db.getconnection("amavis_quarantine")
    try:
        max_msg_days = getattr(settings, "MAX_MESSAGES_AGE")
    except AttributeError:
        max_messages_age = 14

    print "Deleting messages older than %d days..." % max_msg_days
    db.execute(conn, """
DELETE FROM msgs WHERE time_num < UNIX_TIMESTAMP()-%d*24*3600;
""" % max_msg_days)

    print "Deleting unreferenced e-mail addresses..."
    db.execute(conn, """
DELETE FROM maddr
  WHERE NOT EXISTS (SELECT 1 FROM msgs WHERE sid=id)
  AND NOT EXISTS (SELECT 1 FROM msgrcpt WHERE rid=id);
""")

    print "Optimizing tables..."
    db.execute(conn, """
OPTIMIZE TABLE msgs, msgrcpt, quarantine, maddr;
""")

    db.close(conn)

    print "Done."

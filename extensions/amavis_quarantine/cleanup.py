#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb

host = "localhost"
dbname = "amavis"
user = "root"
password = "toto"

max_msg_days = "14"

if __name__ == "__main__":
    conn = MySQLdb.connect(host=host, db=dbname, user=user, passwd=password)
    cursor = conn.cursor()

    print "Deleting messages older than %s days..." % max_msg_days
    cursor.execute("""
DELETE FROM msgs WHERE time_num < UNIX_TIMESTAMP()-%s*24*3600;
""" % max_msg_days)

    conn.commit()

    print "Deleting unreferenced e-mail addresses..."
    cursor.execute("""
DELETE FROM maddr
  WHERE NOT EXISTS (SELECT 1 FROM msgs WHERE sid=id)
  AND NOT EXISTS (SELECT 1 FROM msgrcpt WHERE rid=id);
""")
    conn.commit()

    print "Optimizing tables..."
    cursor.execute("""
OPTIMIZE TABLE msgs, msgrcpt, quarantine, maddr;
""")
    conn.commit()

    conn.close()

    print "Done."

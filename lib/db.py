# -*- coding: utf-8 -*-

"""

"""
import re
import MySQLdb

connections = {}

def mysql_newconnection(host, dbname, login, password):
    import MySQLdb
    return MySQLdb.connect(host=host, db=dbname, user=login, passwd=password)

def getconnection(name):
    if not name in connections.keys():
        from django.conf import settings
        
        cfg = settings.DB_CONNECTIONS[name]
        if cfg["driver"] == "mysql":
            conn = mysql_newconnection(cfg["host"], cfg["dbname"], cfg["login"], 
                                       cfg["password"])
        connections[name] = conn
    return connections[name]
        
def execute(conn, query):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        if re.search("INSERT|DELETE|UPDATE", query):
            conn.commit()
            return (True, None)
        return (True, cursor)
    except MySQLdb.Error, e:
        return (False, "Error %d: %s" % (e.args[0], e.args[1]))

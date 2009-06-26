# -*- coding: utf-8 -*-

"""

"""
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
        

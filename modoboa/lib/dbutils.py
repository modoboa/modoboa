# coding: utf-8
from django.db import connection
from django.conf import settings
            
def db_table_exists(table, cursor=None):
    """Check if table exists

    Taken from here:
    https://gist.github.com/527113/307c2dec09ceeb647b8fa1d6d49591f3352cb034

    """
    try:
        if not cursor:
            cursor = connection.cursor()
        if not cursor:
            raise Exception
        table_names = connection.introspection.get_table_list(cursor)
    except:
        raise Exception("unable to determine if the table '%s' exists" % table)
    else:
        return table in table_names

def db_type(connection="default"):
    """Return the type of the *default* database

    Supported values : 'postgres', 'mysql', 'sqlite'

    :return: a string or None
    """
    for t in ['postgres', 'mysql', 'sqlite']:
        if settings.DATABASES[connection]['ENGINE'].find(t) != -1:
            return t
    return None

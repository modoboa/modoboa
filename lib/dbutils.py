# coding: utf-8
from django.db import connection
            
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

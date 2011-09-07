#!/usr/bin/env python
# coding: utf-8

"""
Simple script to remove useless records from the database (like orphan
User records).
"""

from django.contrib.auth.models import User
from modoboa.admin.models import Mailbox

def dbcleanup():
    print "Starting database cleanup"
    for user in User.objects.all():
        if user.id != 1 and not len(user.mailbox_set.all()):
            print "Removing orphan user %s" % user.username
            user.delete()
    print "Done"

if __name__ == "__main__":
    dbcleanup()


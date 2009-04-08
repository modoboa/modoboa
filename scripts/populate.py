#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group, Permission

if __name__ == "__main__":
    grp = Group()
    grp.name = "DomainAdmins"
    grp.save()
    
    for pcode in  ["add_mailbox", "change_mailbox", "delete_mailbox", "add_alias", 
                   "change_alias", "delete_alias", "view_domain", "view_mailboxes",
                   "view_aliases"]:
        grp.permissions.add(Permission.objects.get(codename=pcode))
    grp.save()

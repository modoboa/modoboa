#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group

if __name__ == "__main__":
    for gname in ["DomainAdmins", "Users"]:
        grp = Group()
        grp.name = gname
        grp.save()

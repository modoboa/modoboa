#!/usr/bin/env python
# coding: utf-8

import time
from optparse import make_option
from django.core.management.base import BaseCommand
from modoboa.lib import parameters
from modoboa.extensions.amavis import Amavis
from modoboa.extensions.amavis.models import *

class Command(BaseCommand):
    args = ''
    help = 'Amavis quarantine cleanup'

    option_list = BaseCommand.option_list + (
        make_option('--debug',
                    action='store_true',
                    default=False,
                    help='Activate debug output'),
        )

    def handle(self, *args, **options):
        if options["debug"]:
            import logging
            l = logging.getLogger("django.db.backends")
            l.setLevel(logging.DEBUG)
            l.addHandler(logging.StreamHandler())

        Amavis().load()

        max_messages_age = int(parameters.get_admin("MAX_MESSAGES_AGE",
                                                    app="amavis"))

        flags = ['D']
        if parameters.get_admin("RELEASED_MSGS_CLEANUP", 
                                app="amavis") == "yes":
            flags += ['R']

        print "Deleting marked messages..."
        ids = Msgrcpt.objects.filter(rs__in=flags).values("mail_id")
        for msg in Msgs.objects.filter(mail_id__in=ids):
            if not msg.msgrcpt_set.exclude(rs__in=flags).count():
                msg.delete()
        
        print "Deleting messages older than %d days..." % max_messages_age
        limit = int(time.time()) - (max_messages_age * 24 * 3600)
        Msgs.objects.filter(time_num__lt=limit).delete()

        print "Deleting unreferenced e-mail addresses..."
        for maddr in Maddr.objects.all():
            if not len(maddr.msgs_set.all()) and not len(maddr.msgrcpt_set.all()):
                maddr.delete()
    
        print "Done."

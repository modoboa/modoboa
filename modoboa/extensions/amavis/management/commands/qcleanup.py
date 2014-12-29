#!/usr/bin/env python
# coding: utf-8

import time
from optparse import make_option

from django.core.management.base import BaseCommand

from modoboa.core.management.commands import CloseConnectionMixin
from modoboa.extensions.amavis import Amavis
from modoboa.extensions.amavis.models import (
    Msgrcpt, Msgs, Maddr
)
from modoboa.lib import parameters


class Command(BaseCommand, CloseConnectionMixin):
    args = ''
    help = 'Amavis quarantine cleanup'

    option_list = BaseCommand.option_list + (
        make_option('--debug',
                    action='store_true',
                    default=False,
                    help='Activate debug output'),
        make_option('--verbose',
                    action='store_true',
                    default=False,
                    help='Display informational messages')
    )

    def __vprint(self, msg):
        if not self.verbose:
            return
        print msg

    def handle(self, *args, **options):
        if options["debug"]:
            import logging
            l = logging.getLogger("django.db.backends")
            l.setLevel(logging.DEBUG)
            l.addHandler(logging.StreamHandler())
        self.verbose = options["verbose"]

        Amavis().load()

        max_messages_age = int(parameters.get_admin("MAX_MESSAGES_AGE",
                                                    app="amavis"))

        flags = ['D']
        if parameters.get_admin("RELEASED_MSGS_CLEANUP",
                                app="amavis") == "yes":
            flags += ['R']

        self.__vprint("Deleting marked messages...")
        ids = Msgrcpt.objects.filter(rs__in=flags).values("mail_id").distinct()
        for msg in Msgs.objects.filter(mail_id__in=ids):
            if not msg.msgrcpt_set.exclude(rs__in=flags).count():
                msg.delete()

        self.__vprint(
            "Deleting messages older than %d days..." % max_messages_age)
        limit = int(time.time()) - (max_messages_age * 24 * 3600)
        Msgs.objects.filter(time_num__lt=limit).delete()

        self.__vprint("Deleting unreferenced e-mail addresses...")
        for maddr in Maddr.objects.all():
            if not maddr.msgs_set.count() and not maddr.msgrcpt_set.count():
                maddr.delete()

        self.__vprint("Done.")

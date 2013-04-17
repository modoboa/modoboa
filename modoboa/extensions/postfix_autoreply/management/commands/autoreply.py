#!/usr/bin/env python
# coding: utf-8

import sys
import datetime
from django.core.management.base import BaseCommand, CommandError
from modoboa.lib import parameters
from modoboa.lib.emailutils import split_mailbox, sendmail_simple
from modoboa.admin.models import Mailbox
from modoboa.extensions.postfix_autoreply import PostfixAutoreply
from modoboa.extensions.postfix_autoreply.models import ARmessage, ARhistoric

def send_autoreply(sender, mailbox, armessage):
    if armessage.untildate is not None \
        and armessage.untildate < datetime.datetime.today():
        armessage.enabled = False
        armessage.save()
        return

    try:
        lastar = ARhistoric.objects.get(armessage=armessage.id, sender=sender)
        PostfixAutoreply().load()
        timeout = parameters.get_admin("AUTOREPLIES_TIMEOUT", 
                                       app="postfix_autoreply")
        delta = datetime.timedelta(seconds=int(timeout))
        if lastar.last_sent + delta > datetime.datetime.now():
            sys.exit(0)
    except ARhistoric.DoesNotExist:
        lastar = ARhistoric()
        lastar.armessage = armessage
        lastar.sender = sender

    sendmail_simple(mailbox.name_and_address, sender, armessage.subject,
                    armessage.content.encode('utf-8'))
    
    lastar.last_sent = datetime.datetime.now()
    lastar.save()


class Command(BaseCommand):
    args = '<sender> <recipient ...>'
    help = 'Send autoreply emails'

    def handle(self, *args, **options):
        if len(args) < 2:
            raise CommandError("usage: ./manage.py autoreply <sender> <recipient ...>")

        sender = args[0]
        for fulladdress in args[1:]:
            address, domain = split_mailbox(fulladdress)
            try:
                mbox = Mailbox.objects.get(address=address, domain__name=domain)
            except Mailbox.DoesNotExist:
                print "Unknown recipient %s" % (mbox)
                continue
            try:
                armessage = ARmessage.objects.get(mbox=mbox.id, enabled=True)
            except ARmessage.DoesNotExist:
                continue

            send_autoreply(sender, mbox, armessage)

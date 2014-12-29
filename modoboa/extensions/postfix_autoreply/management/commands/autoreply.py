#!/usr/bin/env python
# coding: utf-8
import sys
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from modoboa.core.management.commands import CloseConnectionMixin
from modoboa.lib import parameters
from modoboa.lib.emailutils import split_mailbox, sendmail_simple
from modoboa.extensions.admin.models import Mailbox
from modoboa.extensions.postfix_autoreply import PostfixAutoreply
from modoboa.extensions.postfix_autoreply.models import ARmessage, ARhistoric


def send_autoreply(sender, mailbox, armessage):
    if armessage.fromdate > timezone.now():
        return
    if armessage.untildate is not None \
        and armessage.untildate < timezone.now():
        armessage.enabled = False
        armessage.save()
        return

    try:
        lastar = ARhistoric.objects.get(armessage=armessage.id, sender=sender)
        PostfixAutoreply().load()
        timeout = parameters.get_admin("AUTOREPLIES_TIMEOUT",
                                       app="postfix_autoreply")
        delta = datetime.timedelta(seconds=int(timeout))
        now = timezone.make_aware(datetime.datetime.now(),
                                  timezone.get_default_timezone())
        if lastar.last_sent + delta > now:
            sys.exit(0)
    except ARhistoric.DoesNotExist:
        lastar = ARhistoric()
        lastar.armessage = armessage
        lastar.sender = sender

    sendmail_simple(mailbox.user.encoded_address, sender, armessage.subject,
                    armessage.content.encode('utf-8'))

    lastar.last_sent = datetime.datetime.now()
    lastar.save()


class Command(BaseCommand, CloseConnectionMixin):
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
                print "Unknown recipient %s" % (fulladdress)
                continue
            try:
                armessage = ARmessage.objects.get(mbox=mbox.id, enabled=True)
            except ARmessage.DoesNotExist:
                continue

            send_autoreply(sender, mbox, armessage)

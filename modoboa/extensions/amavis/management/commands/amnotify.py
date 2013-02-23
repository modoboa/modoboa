#!/usr/bin/env python
# coding: utf-8

import sys
import os
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import parameters
from modoboa.lib.emailutils import sendmail_simple
from modoboa.admin.models import User, Domain
from modoboa.extensions.amavis import Amavis
from modoboa.extensions.amavis.models import *
from modoboa.extensions.amavis.sql_listing import get_wrapper


class Command(BaseCommand):
    help = 'Amavis notification tool'

    sender = None
    baseurl = None
    listingurl = None

    option_list = BaseCommand.option_list + (
        make_option("--baseurl", type="string", default=None,
                    help="The scheme and hostname used to access Modoboa"),
        make_option("--smtp_host", type="string", default="localhost",
                    help="The address of the SMTP server used to send notifications"),
        make_option("--smtp_port", type="int", default=25,
                    help="The listening port of the SMTP server used to send notifications"),
        make_option("--verbose", action="store_true",
                    help="Activate verbose mode")
    )

    def handle(self, *args, **options):
        if options["baseurl"] is None:
            raise CommandError("You must provide the --baseurl option")
        self.options = options
        Amavis().load()
        self.notify_admins_pending_requests()

    def send_pr_notification(self, rcpt, reqs):
        if self.options["verbose"]:
            print "Sending notification to %s" % rcpt
        total = len(reqs)
        reqs = reqs.all()[:10]
        content = render_to_string(
            "amavis/notifications/pending_requests.html", dict(
                total=total, requests=reqs,
                baseurl=self.baseurl, listingurl=self.listingurl
            )
        )
        status, msg = sendmail_simple(
            self.sender, rcpt,
            subject=_("[modoboa] Pending release requests"),
            content=content,
            server=self.options["smtp_host"],
            port=self.options["smtp_port"]
        )
        if not status:
            print msg

    def notify_admins_pending_requests(self):
        self.sender = parameters.get_admin("NOTIFICATIONS_SENDER",
                                           app="amavis")
        self.baseurl = self.options["baseurl"].strip("/")
        self.listingurl = self.baseurl + reverse("modoboa.extensions.amavis.views._listing") + "?viewrequests=1"

        for da in User.objects.filter(groups__name="DomainAdmins"):
            if not da.has_mailbox:
                continue
            rcpt = da.mailbox_set.all()[0].full_address
            reqs = get_wrapper().get_domains_pending_requests(da.get_domains())
            if len(reqs):
                self.send_pr_notification(rcpt, reqs)

        reqs = Msgrcpt.objects.filter(rs='p')
        if not len(reqs):
            if self.options["verbose"]:
                print "No release request currently pending"
            return
        for su in User.objects.filter(is_superuser=True):
            if not su.has_mailbox:
                continue
            rcpt = su.mailbox_set.all()[0].full_address
            self.send_pr_notification(rcpt, reqs)

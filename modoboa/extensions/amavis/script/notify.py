#!/usr/bin/env python
# coding: utf-8

import sys, os
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import parameters
from modoboa.lib.emailutils import sendmail_simple
from modoboa.admin.models import User, Domain
from modoboa.extensions.amavis import Amavis
from modoboa.extensions.amavis.models import *

sender = None
baseurl = None
listingurl = None

def send_pr_notification(rcpt, reqs):
    total = len(reqs)
    reqs = reqs.all()[:10]
    content = render_to_string("amavis/notifications/pending_requests.html", dict(
            total=total, requests=reqs, baseurl=baseurl, listingurl=listingurl
            ))
    sendmail_simple(sender, rcpt, subject=_("[modoboa] Pending release requests"),
                    content=content, server=options.smtp_host, port=options.smtp_port)

def notify_admins_pending_requests():
    sender = parameters.get_admin("NOTIFICATIONS_SENDER", app="amavis")
    baseurl = options.baseurl.strip("/")
    listingurl = baseurl + reverse("modoboa.extensions.amavis.views._listing") + "?viewrequests=1"
    for da in User.objects.filter(groups__name="DomainAdmins"):
        if not da.has_mailbox:
            continue
        rcpt = da.mailbox_set.all()[0].full_address
        regexp = "(%s)" % '|'.join(map(lambda dom: dom.name, da.get_domains()))
        reqs = Msgrcpt.objects.filter(rs='p', rid__email__regex=regexp)
        if len(reqs):
            send_pr_notification(rcpt, reqs)

    reqs = Msgrcpt.objects.filter(rs='p')
    if not len(reqs):
        return
    for su in User.objects.filter(is_superuser=True):
        if not su.has_mailbox:
            continue
        rcpt = su.mailbox_set.all()[0].full_address
        send_pr_notification(rcpt, reqs)

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--baseurl", type="string", default=None,
                      help="The scheme and hostname used to access Modoboa")
    parser.add_option("--smtp_host", type="string", default="localhost",
                      help="The address of the SMTP server used to send notifications")
    parser.add_option("--smtp_port", type="int", default=25,
                      help="The listening port of the SMTP server used to send notifications")
    options, args = parser.parse_args()

    if not options.baseurl:
        print >>sys.stderr, "You must provide the --baseurl option"
        sys.exit(2)

    Amavis().load()
    sender = parameters.get_admin("NOTIFICATIONS_SENDER", app="amavis")
    baseurl = options.baseurl.strip("/")
    listingurl = baseurl + reverse("modoboa.extensions.amavis.views._listing") + "?viewrequests=1"
    notify_admins_pending_requests()
    

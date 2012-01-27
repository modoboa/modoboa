#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import smtplib
from email.mime.text import MIMEText
import datetime
from modoboa.lib import parameters
from modoboa.lib.emailutils import split_mailbox
from modoboa.admin.models import Mailbox
from modoboa.extensions.postfix_autoreply import main
from modoboa.extensions.postfix_autoreply.models import ARmessage, ARhistoric

def send_autoreply(sender, mailbox, armessage):
    if armessage.untildate is not None \
            and armessage.untildate < datetime.datetime.now():
        armessage.enabled = False
        armessage.save()
        return

    try:
        lastar = ARhistoric.objects.get(armessage=armessage.id, sender=sender)
        main.load()
        timeout = parameters.get_admin("AUTOREPLIES_TIMEOUT", 
                                       app="postfix_autoreply")
        delta = datetime.timedelta(seconds=int(timeout))
        if lastar.last_sent + delta > datetime.datetime.now():
            sys.exit(0)
    except ARhistoric.DoesNotExist:
        lastar = ARhistoric()
        lastar.armessage = armessage
        lastar.sender = sender

    msg = MIMEText(armessage.content.encode('utf-8'), _charset='utf-8')
    msg['Subject'] = armessage.subject
    msg['From'] = mailbox.full_address
    msg['To'] = sender
    
    s = smtplib.SMTP()
    s.connect()
    s.sendmail(mailbox.full_address, sender, msg.as_string())
    s.quit()
    
    lastar.last_sent = datetime.datetime.now()
    lastar.save()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Not enough arguments, aborting."
        sys.exit(1)

    sender = sys.argv[1]
    for fulladdress in sys.argv[2:]:
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

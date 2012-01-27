# coding: utf-8
"""
Postfix auto-replies plugin.

This module provides a way to integrate Modoboa auto-reply
functionality into Postfix.

"""
from django.conf.urls.defaults import include
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_noop as _, ugettext
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url
from models import *

def infos():
    return {
        "name" : "Postfix autoreply",
        "version" : "1.0",
        "description" : ugettext("Auto-reply (vacation) functionality using Postfix"),
        "url" : "postfix_autoreply"
        }

def load():
    parameters.register_admin(
        "AUTOREPLIES_TIMEOUT", 
        type="int", deflt=86400,
        help=_("Timeout in seconds between two auto-replies to the same recipient")
        )

def destroy():
    events.unregister("CreateDomain", onCreateDomain)
    events.unregister("DeleteDomain", onDeleteDomain)
    events.unregister("CreateMailbox", onCreateMailbox)
    events.unregister("DeleteMailbox", onDeleteMailbox)
    events.unregister("ModifyMailbox", onModifyMailbox)
    events.unregister("UserMenuDisplay", menu)
    parameters.unregister_app("postfix_autoreply")

@events.observe("UserMenuDisplay")
def menu(target, user):
    import views

    if target != "uprefs_menu":
        return []
    if not user.has_mailbox:
        return []
    return [
        {"name" : "autoreply",
         "url" : reverse(views.autoreply),
         "img" : static_url("pics/auto-reply.png"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:440,y:400}}",
         "label" : ugettext("Auto-reply message")}
        ]

@events.observe("CreateDomain")
def onCreateDomain(user, domain):
    transport = Transport()
    transport.domain = "autoreply.%s" % domain.name
    transport.method = "autoreply:"
    transport.save()

@events.observe("DeleteDomain")
def onDeleteDomain(domain):
    trans = Transport.objects.get(domain="autoreply.%s" % domain.name)
    trans.delete()

@events.observe("CreateMailbox")
def onCreateMailbox(user, mailbox):
    alias = Alias()
    alias.full_address = mailbox.full_address
    alias.autoreply_address = \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()

@events.observe("DeleteMailbox")
def onDeleteMailbox(mailbox):
    try:
        alias = Alias.objects.get(full_address=mailbox.full_address)
        alias.delete()
    except Alias.DoesNotExist:
        pass

@events.observe("ModifyMailbox")
def onModifyMailbox(mailbox, oldmailbox):
    if oldmailbox.full_address == mailbox.full_address:
        return
    alias = Alias.objects.get(full_address=oldmailbox.full_address)
    alias.full_address = mailbox.full_address
    alias.autoreply_address =  \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()

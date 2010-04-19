# -*- coding: utf-8 -*-

"""
Postfix auto-replies plugin.

This module provides a way to integrate MailNG auto-reply
functionality into Postfix.

"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from mailng.lib import events, parameters
from mailng import main
from models import Transport, Alias

def init():
    events.register("CreateDomain", onCreateDomain)
    events.register("DeleteDomain", onDeleteDomain)
    events.register("CreateMailbox", onCreateMailbox)
    events.register("DeleteMailbox", onDeleteMailbox)
    events.register("ModifyMailbox", onModifyMailbox)

    events.register("UserMenuDisplay", menu)

    parameters.register("postfix_autoreply", "AUTOREPLIES_TIMEOUT", "int", 86400,
                        help=_("Timeout in seconds between two auto-replies to the same recipient"))

def urls():
    return ()

def menu(**kwargs):
    if kwargs["target"] != "user_menu_bar":
        return []
    return [
        {"name" : "autoreply",
         "url" : reverse(main.views.autoreply),
         "img" : "/static/pics/auto-reply.png",
         "label" : _("Auto-reply message")}
        ]

def onCreateDomain(**kwargs):
    dom = kwargs["dom"]
    transport = Transport()
    transport.domain = "autoreply.%s" % dom.name
    transport.method = "autoreply:"
    transport.save()

def onDeleteDomain(**kwargs):
    dom = kwargs["dom"]
    trans = Transport.objects.get(domain="autoreply.%s" % dom.name)
    trans.delete()

def onCreateMailbox(**kwargs):
    mbox = kwargs["mbox"]
    alias = Alias()
    alias.full_address = mbox.full_address
    alias.autoreply_address = \
        "%s@autoreply.%s" % (mbox.full_address, mbox.domain.name)
    alias.save()

def onDeleteMailbox(**kwargs):
    mbox = kwargs["mbox"]
    try:
        alias = Alias.objects.get(full_address=mbox.full_address)
        alias.delete()
    except Alias.DoesNotExist:
        pass

def onModifyMailbox(**kwargs):
    mbox = kwargs["mbox"]
    oldmbox = kwargs["oldmbox"]
    if oldmbox.full_address == mbox.full_address:
        return
    alias = Alias.objects.get(full_address=oldmbox.full_address)
    alias.full_address = mbox.full_address
    alias.autoreply_address =  \
        "%s@autoreply.%s" % (mbox.full_address, mbox.domain.name)
    alias.save()

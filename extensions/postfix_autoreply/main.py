# -*- coding: utf-8 -*-

"""
Postfix auto-replies plugin.

This module provides a way to integrate MailNG auto-reply
functionality into Postfix.

"""
from mailng.lib import events
from models import Transport, Alias

def init():
    events.register("CreateDomain", onCreateDomain)
    events.register("DeleteDomain", onDeleteDomain)
    events.register("CreateMailbox", onCreateMailbox)
    events.register("DeleteMailbox", onDeleteMailbox)

def onCreateDomain(**kwargs):
    dom = kwargs["dom"]
    transport = Transport()
    transport.domain = "autoreply.%s" % dom.name
    transport.method = "autoreply:"
    transport.save()

def onDeleteDomain(**kwargs):
    dom = kwargs["dom"]
    trans = Transport.objects.get(domain="autoreply.%s" % dom.name)
    trabs.delete()

def onCreateMailbox(**kwargs):
    mbox = kwargs["mbox"]
    alias = Alias()
    alias.full_address = mbox.full_address
    alias.autoreply_address = \
        "%s@autoreply.%s" % (mbox.full_address, mbox.domain.name)
    alias.save()

def onDeleteMailbox(**kwargs):
    mbox = kwargs["mbox"]
    alias = Alias.objects.get(full_address=mbox.full_address)
    alias.delete()

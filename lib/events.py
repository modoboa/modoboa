# -*- coding: utf-8 -*-

"""
This module provides a simple way of managing events between MailNG
core application and additional components.

"""

events = ["CreateDomain",
          "DeleteDomain",
          "CreateMailbox",
          "DeleteMailbox"]

callbacks = {}

def register(event, callback):
    if not event in events:
        return 0
    if not event in callbacks.keys():
        callbacks[event] = []
    callbacks[event].append(callback)
    return 1

def raiseEvent(event, **kwargs):
    if not event in events or not event in callbacks.keys():
        return 0
    for callback in callbacks[event]:
        callback(**kwargs)
    return 1

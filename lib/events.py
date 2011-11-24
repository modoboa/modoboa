# -*- coding: utf-8 -*-

"""
This module provides a simple way of managing events between Modoboa
core application and additional components.

"""

events = ["CreateDomain",
          "DeleteDomain",
          "CreateMailbox",
          "DeleteMailbox",
          "ModifyMailbox",

          "PasswordChange",

          "UserMenuDisplay",
          "AdminMenuDisplay",

          "PermsGetTables",
          "PermsGetClass",

          "ExtEnabled",
          "ExtDisabled",

          "UserLogin",
          "UserLogout",

          "GetAnnouncement"]

callbacks = {}

def register(event, callback):
    """Register a plugin callback for a specific event

    The event must be declared in this module.

    :param event: the event to listen to
    :param callback: a function to execute when the event is raised
    """
    if not event in events:
        return 0
    if not event in callbacks.keys():
        callbacks[event] = []
    if not callback in callbacks[event]:
        callbacks[event].append(callback)
    return 1

def unregister(event, callback):
    """Unregister a callback for a specific event

    :param event: the targeted event
    :param callback: the callback to remove
    """
    if not event in events:
        return False
    if not callbacks.has_key(event):
        return False
    try:
        callbacks[event].remove(callback)
    except ValueError:
        pass

def raiseEvent(event, **kwargs):
    """Raise a specific event

    Any additional keyword argument will be passed to registered
    callbacks.

    :param event: the event to raise
    """
    if not event in events or not event in callbacks.keys():
        return 0
    for callback in callbacks[event]:
        callback(**kwargs)
    return 1

def raiseQueryEvent(event, **kwargs):
    """Raise a specific event and wait for answers from callbacks

    Any additional keyword argument will be passed to registered
    callbacks. Callback answers are returned as a list.

    :param event: the event to raise
    """
    result = []
    if not event in events or not event in callbacks.keys():
        return result
    for callback in callbacks[event]:
        result += callback(**kwargs)
    return result

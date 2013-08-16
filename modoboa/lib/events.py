# -*- coding: utf-8 -*-

"""
:mod:`events` --- simple events handling
----------------------------------------

This module provides a simple way of managing events between Modoboa
core application and additional components.

"""
from functools import wraps
import inspect
import re
from django.conf import settings

events = [
    "CanCreate",

    "CreateDomain",
    "DomainModified",
    "DeleteDomain",

    "DomainAliasCreated",
    "DomainAliasDeleted",

    "CreateMailbox",
    "DeleteMailbox",
    "ModifyMailbox",

    "MailboxAliasCreated",
    "MailboxAliasDeleted",

    "AccountCreated",
    "AccountModified",
    "AccountDeleted",
    "PasswordUpdated",
    "ExtraAccountActions",

    "PasswordChange",
    
    "UserMenuDisplay",
    "AdminMenuDisplay",
    "GetStaticContent",

    "ExtraAccountForm",
    "CheckExtraAccountForm",
    "FillAccountInstances",

    "ExtraDomainForm",
    "FillDomainInstances",
    
    "GetExtraRoles",
    
    "ExtEnabled",
    "ExtDisabled",

    "UserLogin",
    "UserLogout",
    
    "GetAnnouncement",

    "TopNotifications",
    "ExtraAdminContent",

    "ExtraUprefsRoutes",
    "ExtraUprefsJS"
    ]

callbacks = {}

def registerEvent(name):
    """Register a new event

    :param name: the event's name
    """
    if not name in events:
        events.append(name)

def register(event, callback):
    """Register a plugin callback for a specific event

    The event must be declared in this module.

    :param event: the event to listen to
    :param callback: a function to execute when the event is raised
    """
    # if not event in events:
    #     print "Event %s not registered" % event
    #     return 0
    if not event in callbacks.keys():
        callbacks[event] = {}
    fullname = "%s.%s" % (callback.__module__, callback.__name__)
    if not callbacks[event].has_key(fullname):
        callbacks[event][fullname] = callback
    return 1

class observe(object):
    """Event observing decorator

    Automatically register the decorated function to observe the given
    event. If the decorated function is located into an extension, we
    check before each call if the extension is enabled or not. If
    that's not the case, the callback is not called.

    .. note::

        That's not a really optimized behaviour but I haven't found
        another solution to achieve that feature.

    :param evtname: the event's name
    """
    def __init__(self, *evtnames, **kwargs):
        self.evtnames = evtnames
        if kwargs.has_key("extname"):
            self.extname = kwargs["extname"]

    def __guess_extension_name(self, modname):
        if modname.startswith('modoboa.extensions'):
            m = re.match(r'modoboa\.extensions\.([^\.]+)', modname)
            if m:
                return m.group(1)
        return None

    def __call__(self, f):
        modname = inspect.getmodule(inspect.stack()[1][0]).__name__
        extname = self.extname if hasattr(self, "extname") else self.__guess_extension_name(modname)
        @wraps(f)
        def wrapped_f(*args):
            if extname:
                from modoboa.core.models import Extension
                from modoboa.core.extensions import exts_pool
                try:
                    ext = Extension.objects.get(name=extname)
                except Extension.DoesNotExist:
                    extdef = exts_pool.get_extension(extname)
                    if not extdef.always_active:
                        return []
                else:
                    if not ext.enabled:
                        return []
            elif not modname in settings.MODOBOA_APPS:
                return []
                
            return f(*args)

        map(lambda evt: register(evt, wrapped_f), self.evtnames)
        return wrapped_f

def unregister(event, callback):
    """Unregister a callback for a specific event

    :param event: the targeted event
    :param callback: the callback to remove
    """
    if not event in events:
        return False
    if not callbacks.has_key(event):
        return False
    fullname = "%s.%s" % (callback.__module__, callback.__name__)
    try:
        del callbacks[event][fullname]
    except KeyError:
        pass

def raiseEvent(event, *args):
    """Raise a specific event

    Any additional keyword argument will be passed to registered
    callbacks.

    :param event: the event to raise
    """
    if not event in events or not event in callbacks.keys():
        return 0
    for name, callback in callbacks[event].iteritems():
        callback(*args)
    return 1

def raiseQueryEvent(event, *args):
    """Raise a specific event and wait for answers from callbacks

    Any additional keyword argument will be passed to registered
    callbacks. Callback answers are returned as a list.

    :param event: the event to raise
    """
    result = []
    if not event in events or not event in callbacks.keys():
        return result
    for name, callback in callbacks[event].iteritems():
        result += callback(*args)
    return result

def raiseDictEvent(event, *args):
    """Raise a specific event and return result as a dictionnary

    Any additional keyword argument will be passed to registered
    callbacks. Callback answers must be dictionnaries.

    :param event: the event to raise
    :return: a dictionnary
    """
    result = {}
    if not event in events or not event in callbacks.keys():
        return result
    for name, callback in callbacks[event].iteritems():
        tmp = callback(*args)
        for k, v in tmp.iteritems():
            result[k] = v
    return result

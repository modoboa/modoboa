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
from modoboa.lib.sysutils import guess_extension_name

events = []
callbacks = {}


def declare(nevents):
    """Declare new events

    :param list nevents: a list of event names
    """
    for evt in nevents:
        if not evt in events:
            events.append(evt)


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
    if not fullname in callbacks[event]:
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
        if "extname" in kwargs:
            self.extname = kwargs["extname"]

    def __guess_extension_name(self, modname):
        if modname.startswith('modoboa.extensions'):
            m = re.match(r'modoboa\.extensions\.([^\.]+)', modname)
            if m:
                return m.group(1)
        return None

    def __call__(self, f):
        modname = inspect.getmodule(inspect.stack()[1][0]).__name__
        extname = self.extname if hasattr(self, "extname") \
            else self.__guess_extension_name(modname)

        @wraps(f)
        def wrapped_f(*args, **kwargs):
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
                        return None
            elif not modname in settings.MODOBOA_APPS:
                return []
            return f(*args, **kwargs)
        for evt in self.evtnames:
            register(evt, wrapped_f)
        return wrapped_f


def unregister(event, callback):
    """Unregister a callback for a specific event

    :param event: the targeted event
    :param callback: the callback to remove
    """
    if not event in events:
        return False
    if not event in callbacks:
        return False
    fullname = "%s.%s" % (callback.__module__, callback.__name__)
    try:
        del callbacks[event][fullname]
    except KeyError:
        pass


def unregister_extension(extension=None):
    """Unregister all callbacks declared by an extension.

    :param str extension: extension full name (ie. module name)
    """
    if extension is None:
        extension = guess_extension_name()
    for evt, values in callbacks.items():
        for name in values.keys():
            if extension in name:
                del callbacks[evt][name]


def raiseEvent(event, *args, **kwargs):
    """Raise a specific event

    Any additional keyword argument will be passed to registered
    callbacks.

    :param event: the event to raise
    """
    if not event in events or not event in callbacks:
        return 0
    for callback in callbacks[event].values():
        callback(*args, **kwargs)
    return 1


def raiseQueryEvent(event, *args, **kwargs):
    """Raise a specific event and wait for answers from callbacks

    Any additional keyword argument will be passed to registered
    callbacks. Callback answers are returned as a list.

    :param event: the event to raise
    """
    result = []
    if not event in events or not event in callbacks:
        return result
    for callback in callbacks[event].values():
        tmp = callback(*args, **kwargs)
        if tmp is None:
            # Callback is registered but associated extension is
            # disabled.
            continue
        result += tmp
    return result


def raiseDictEvent(event, *args):
    """Raise a specific event and return result as a dictionnary

    Any additional keyword argument will be passed to registered
    callbacks. Callback answers must be dictionnaries.

    :param event: the event to raise
    :return: a dictionnary
    """
    result = {}
    if not event in events or not event in callbacks:
        return result
    for callback in callbacks[event].values():
        tmp = callback(*args)
        if tmp is None:
            # Callback is registered but associated extension is
            # disabled.
            continue
        for k, v in tmp.iteritems():
            result[k] = v
    return result

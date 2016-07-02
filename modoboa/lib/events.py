# -*- coding: utf-8 -*-

"""
:mod:`EVENTS` --- simple EVENTS handling
----------------------------------------

This module provides a simple way of managing EVENTS between Modoboa
core application and additional components.

"""

EVENTS = []
CALLBACKS = {}


def declare(nevents):
    """Declare new events.

    :param list nevents: a list of event names
    """
    for evt in nevents:
        if evt not in EVENTS:
            EVENTS.append(evt)


def register(event, callback):
    """Register a plugin callback for a specific event

    The event must be declared in this module.

    :param event: the event to listen to
    :param callback: a function to execute when the event is raised
    """
    # if not event in EVENTS:
    #     print "Event %s not registered" % event
    #     return 0
    if event not in CALLBACKS.keys():
        CALLBACKS[event] = {}
    fullname = "%s.%s" % (callback.__module__, callback.__name__)
    if fullname not in CALLBACKS[event]:
        CALLBACKS[event][fullname] = callback
    return 1


class observe(object):
    """Event observing decorator.

    Automatically register the decorated function to observe the given
    event.

    :param evtnames: a list of event names
    """
    def __init__(self, *evtnames, **kwargs):
        self.evtnames = evtnames

    def __call__(self, f):
        for evt in self.evtnames:
            register(evt, f)
        return f


def unregister(event, callback):
    """Unregister a callback for a specific event

    :param event: the targeted event
    :param callback: the callback to remove
    """
    if event not in EVENTS:
        return False
    if event not in CALLBACKS:
        return False
    fullname = "%s.%s" % (callback.__module__, callback.__name__)
    try:
        del CALLBACKS[event][fullname]
    except KeyError:
        pass


def raiseEvent(event, *args, **kwargs):
    """Raise a specific event

    Any additional keyword argument will be passed to registered
    CALLBACKS.

    :param event: the event to raise
    """
    if event not in EVENTS or event not in CALLBACKS:
        return 0
    for callback in CALLBACKS[event].values():
        callback(*args, **kwargs)
    return 1


def raiseQueryEvent(event, *args, **kwargs):
    """Raise a specific event and wait for answers from CALLBACKS

    Any additional keyword argument will be passed to registered
    CALLBACKS. Callback answers are returned as a list.

    :param event: the event to raise
    """
    result = []
    if event not in EVENTS or event not in CALLBACKS:
        return result
    for callback in CALLBACKS[event].values():
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
    CALLBACKS. Callback answers must be dictionnaries.

    :param event: the event to raise
    :return: a dictionnary
    """
    result = {}
    if event not in EVENTS or event not in CALLBACKS:
        return result
    for callback in CALLBACKS[event].values():
        tmp = callback(*args)
        if tmp is None:
            # Callback is registered but associated extension is
            # disabled.
            continue
        for k, v in tmp.iteritems():
            result[k] = v
    return result

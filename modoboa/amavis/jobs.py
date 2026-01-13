"""Async jobs definition."""

from django.core.management import call_command


def amnotify():
    call_command("amnotify")


def qcleanup():
    call_command("qcleanup")

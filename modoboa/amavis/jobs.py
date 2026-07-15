"""Async jobs definition."""

from django.core.management import call_command


def amnotify(*args, **options):
    call_command("amnotify", *args, **options)


def qcleanup(*args, **options):
    call_command("qcleanup", *args, **options)

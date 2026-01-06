"""Async jobs definition."""

from django.core.management import call_command


def logparser():
    call_command("logparser")


def update_statistics():
    call_command("update_statistics")

"""Async jobs definition."""

from django.core.management import call_command


def logparser(*args, **options):
    call_command("logparser", *args, **options)


def update_statistics(*args, **options):
    call_command("update_statistics", *args, **options)

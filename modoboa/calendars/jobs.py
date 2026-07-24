"""Async jobs definition."""

from django.core.management import call_command


def generate_rights(*args, **options):
    call_command("generate_rights", *args, **options)

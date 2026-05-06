"""Async jobs definition."""

from django.core.management import call_command


def generate_offlineimap_config():
    call_command("generate_offlineimap_config")

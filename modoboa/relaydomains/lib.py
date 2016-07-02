"""Internal library."""

from .models import RelayDomain


def import_relaydomain(user, row, formopts):
    """Specific code for relay domains import"""
    RelayDomain().from_csv(user, row)

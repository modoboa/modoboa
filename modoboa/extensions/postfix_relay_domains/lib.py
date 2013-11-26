from django.db import transaction
from .models import RelayDomain, RelayDomainAlias


@transaction.commit_on_success
def import_relaydomain(user, row, formopts):
    """Specific code for relay domains import"""
    RelayDomain().from_csv(user, row)


@transaction.commit_on_success
def import_relaydomainalias(user, row, formopts):
    """Specific code for relay domain aliases import"""
    RelayDomainAlias().from_csv(user, row)

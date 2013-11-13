from modoboa.lib import events
from modoboa.extensions.amavis.lib import (
    create_user_and_policy, update_user_and_policy, delete_user_and_policy,
    create_user_and_use_policy, delete_user
)


@events.observe("RelayDomainCreated")
def on_relay_domain_created(user, rdomain):
    create_user_and_policy(rdomain.name)


@events.observe("RelayDomainModified")
def on_relay_domain_modified(rdomain):
    update_user_and_policy(rdomain.oldname, rdomain.name)


@events.observe("RelayDomainDeleted")
def on_relay_domain_deleted(rdomain):
    delete_user_and_policy(rdomain.name)


@events.observe("RelayDomainAliasCreated")
def on_relay_domain_alias_created(user, rdomainalias):
    create_user_and_use_policy(rdomainalias.name, rdomainalias.target.name)


@events.observe("RelayDomainAliasDeleted")
def on_relay_domain_alias_deleted(rdomainalias):
    delete_user(rdomainalias.name)

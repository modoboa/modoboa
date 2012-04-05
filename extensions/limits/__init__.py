# coding: utf-8

"""
The *limits* extension
----------------------
"""
from django.contrib.auth.models import Permission, Group
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_noop as _, ugettext
from django.core.urlresolvers import reverse
from modoboa.lib import events
from modoboa.lib.webutils import static_url
from models import *
from forms import ResourcePoolForm
import permissions
import controls
import views

baseurl = "limits"

def init():
    from modoboa.admin.models import User

    ct = ContentType.objects.get(app_label="admin", model="domain")
    dagrp = Group.objects.get(name="DomainAdmins")

    grp = Group(name="Resellers")
    grp.save()
    grp.permissions.add(*dagrp.permissions.all())

    ct = ContentType.objects.get_for_model(Permission)
    for pname in ["view_permissions"]:
        perm = Permission.objects.get(content_type=ct, codename=pname)
        grp.permissions.add(perm)

    ct = ContentType.objects.get_for_model(Domain)
    for pname in ["view_domains", "add_domain", "change_domain", "delete_domain"]:
        perm = Permission.objects.get(content_type=ct, codename=pname)
        grp.permissions.add(perm)
    grp.save()

    for user in User.objects.filter(groups__name='DomainAdmins'):
        try:
            controls.create_pool(user)
        except IntegrityError:
            pass

def destroy():
    Group.objects.get(name="Resellers").delete()

def infos():
    return {
        "name" : "Limits",
        "version" : "1.0",
        "description" : ugettext("Limits for objects creation"),
        "url" : baseurl
        }

#@events.observe('AdminFooterDisplay')
def display_pool_usage(user, objtype):
    if user.is_superuser:
        return []
    if objtype == "domaliases":
        objtype = "domain_aliases"
    elif objtype == "mbaliases":
        objtype = "mailbox_aliases"
    try:
        l = user.limitspool.get_limit('%s_limit' % objtype)
    except LimitsPool.DoesNotExist:
        return []
    if l.maxvalue == -2:
        label = _("undefined")
    elif l.maxvalue == -1:
        label = _("unlimited")
    else:
        label = str(l.maxvalue)
    return [_("Pool usage: %s / %s") % (l.curvalue, label)]

@events.observe("DomainAdminActions")
def get_da_actions(user):
    return [
        {"name" : "editpool",
         "url" : reverse(views.edit_limits_pool, args=[user.id]),
         "img" : static_url("pics/settings.png"),
         "title" : _("Edit limits allocated to this domain admin"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:330,y:280}}"},
        ]

@events.observe("ExtraAccountForm")
def extra_account_form(user, account=None):
    if not user.is_superuser and not user.belongs_to_group("Resellers"):
        return []
    if account:
        if not account.belongs_to_group("Resellers") and \
           not account.belongs_to_group("DomainAdmins"):
            return []

    return [
        dict(
            id="resources", title=_("Resources"), cls=ResourcePoolForm
            )
        ]

@events.observe("CheckExtraAccountForm")
def check_form_access(account, form):
    if form["id"] != "resources":
        return [True]
    if not account.belongs_to_group("Resellers") and \
       not account.belongs_to_group("DomainAdmins"):
        return [False]
    return [True]

@events.observe("FillAccountInstances")
def fill_account_instances(user, account, instances):
    if not user.is_superuser and not user.belongs_to_group("Resellers"):
        return
    if not account.belongs_to_group("Resellers") and \
       not account.belongs_to_group("DomainAdmins"):
        return
    instances["resources"] = account

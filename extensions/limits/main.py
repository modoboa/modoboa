# coding: utf-8

"""
The *limits* extension
----------------------


"""
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_noop as _, ugettext
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import include
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url
from models import *
import permissions
import controls
import views

baseurl = "limits"

def init():
    ct = ContentType.objects.get(app_label="admin", model="domain")
    grp = Group.objects.get(name="DomainAdmins")
    for pname in ["view_domains", "add_domain", "change_domain", "delete_domain"]:
        perm = Permission.objects.get(content_type=ct, codename=pname)
        grp.permissions.add(perm)
    grp.save()

def destroy():
    ct = ContentType.objects.get(app_label="admin", model="domain")
    grp = Group.objects.get(name="DomainAdmins")
    for pname in ["view_domains", "add_domain", "change_domain", "delete_domain"]:
        perm = Permission.objects.get(content_type=ct, codename=pname)
        grp.permissions.remove(perm)
    grp.save()

def infos():
    return {
        "name" : "Limits",
        "version" : "1.0",
        "description" : ugettext("Limits for objects creation"),
        "url" : baseurl
        }

def urls(prefix):
    return (r'^%s%s/' % (prefix, baseurl),
            include('modoboa.extensions.limits.urls'))

@events.observe('AdminFooterDisplay')
def display_pool_usage(user, objtype):
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

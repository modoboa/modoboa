# coding: utf-8

"""
The *limits* extension
----------------------


"""
from django.utils.translation import ugettext_noop as _, ugettext
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import include
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url
from models import *
import permissions
import controls

baseurl = "limits"

def init():
    pass

def destroy():
    pass

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


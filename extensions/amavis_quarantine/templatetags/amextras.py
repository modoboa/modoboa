from django import template
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf import settings
from modoboa.lib.webutils import static_url
from modoboa.extensions import amavis_quarantine

register = template.Library()

@register.simple_tag
def viewm_menu(user, mail_id, rcpt):
    options_menu = [
        {"name" : "viewmode", 
         "label" : _("View as plain text"),
         "url" : "?mode=plain&links=0"},
        {"name" : "viewmode", 
         "label" : _("View as HTML"),
         "url" : "?mode=html&links=0"},
        {"name" : "viewmode", 
         "label" : _("Activate links"),
         "url" : "?mode=html&links=1"}
        ]

    entries = [
        {"name" : "back",
         "img" : "icon-arrow-left",
         "url" : "javascript:history.go(-1);",
         "label" : _("Back to list")},
        {"name" : "headers",
         "url" : reverse(amavis_quarantine.views.viewheaders, args=[mail_id]),
         "label" : _("View full headers"),
         "modal" : True,
         "autowidth" : True},
        {"name" : "release",
         "img" : "icon-ok",
         "url" : reverse(amavis_quarantine.views.release, args=[mail_id]) \
             + ("?rcpt=%s" % rcpt if rcpt else ""),
         "label" : _("Release")},
        {"name" : "delete",
         "img" : "icon-remove",
         "url" : reverse(amavis_quarantine.views.delete, args=[mail_id]) \
             + ("?rcpt=%s" % rcpt if rcpt else ""),
         "label" : _("Delete")},
        {"name" : "options",
         "label" : _("Options"),
         "img" : "icon-cog",
         "menu" : options_menu}
        ]

    return render_to_string('common/buttons_list.html', 
                            {"entries" : entries})

@register.simple_tag
def viewm_menu_simple(user, mail_id, rcpt, secret_id=""):
    entries = [
        {"name" : "release",
         "img" : "icon-ok",
         "url" : reverse(amavis_quarantine.views.release, args=[mail_id]) \
             + ("?rcpt=%s" % rcpt \
                    + (("&secret_id=%s" % secret_id) if secret_id != "" else "")),
         "label" : _("Release")},
        {"name" : "delete",
         "img" : "icon-remove",
         "url" : reverse(amavis_quarantine.views.delete, args=[mail_id]) \
             + "?rcpt=%s" % rcpt \
             + ("&secret_id=%s" % secret_id if secret_id != "" else ""),
         "label" : _("Delete")},
        ]

    return render_to_string('common/buttons_list.html', 
                            {"entries" : entries})

@register.simple_tag
def quar_menu(user, nbrequests):
    entries = [
        {"name" : "release-multi",
         "url" : reverse(amavis_quarantine.views.process),
         "img" : "icon-ok",
         "label" : _("Release")},
        {"name" : "delete-multi",
         "img" : "icon-remove",
         "url" : reverse(amavis_quarantine.views.process),
         "label" : _("Delete")},
        {"name" : "select",
         "url" : "",
         "img" : static_url("pics/domains.png"),
         "label" : _("Select"),
         "class" : "menubardropdown",
         "menu" : [
                {"name" : "selectmsgs",
                 "url"  : "",
                 "label" : _("Nothing")},
                {"name" : "selectmsgs",
                 "url" : "S",
                 "label" : _("Spam")},
                {"name" : "selectmsgs",
                 "url" : "H",
                 "label" : _("Bad header")},
                {"name" : "selectmsgs",
                 "url" : "M",
                 "label" : _("Bad MIME")}
                ]
         }
        ]

    if user.group != 'SimpleUsers':
        extraopts = [{"name" : "to", "label" : _("To")}]
    else:
        extraopts = []
    extracontent = render_to_string('common/email_searchbar.html', {
            "MEDIA_URL" : settings.MEDIA_URL,
            "extraopts" : extraopts
            })

    if nbrequests > 0:
        tpl = Template('<div class="btn-group"><a name="viewrequests" href="#" class="btn btn-danger">{{ label }}</a></div>')
        extracontent += tpl.render(Context(dict(
                    label=_("%d pending requests" % nbrequests)
                    )))
    
    return render_to_string('common/buttons_list.html', dict(
            entries=entries, extracontent=extracontent
            ))

from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf import settings
from modoboa.lib import static_url
from modoboa.extensions import amavis_quarantine
from modoboa.admin.lib import is_domain_admin

register = template.Library()

@register.simple_tag
def viewm_menu(selection, backurl, mail_id, rcpt, perms):
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
         "url" : backurl,
         "img" : static_url("pics/back.png"),
         "label" : _("Back to list")},
        {"name" : "headers",
         "url" : reverse(amavis_quarantine.views.viewheaders, args=[mail_id]),
         "img" : static_url("pics/add.png"),
         "label" : _("View full headers"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:600,y:500}}"},
        {"name" : "release",
         "url" : reverse(amavis_quarantine.views.release, args=[mail_id]) \
             + "?rcpt=%s" % rcpt,
         "img" : static_url("pics/release.png"),
         "label" : _("Release"),
         "confirm" : _("Release this message?")},
        {"name" : "delete",
         "url" : reverse(amavis_quarantine.views.delete, args=[mail_id]) \
             + "?rcpt=%s" % rcpt,
         "img" : static_url("pics/remove.png"),
         "label" : _("Delete"),
         "confirm" : _("Delete this message?")},
        {"name" : "options",
         "label" : _("Options"),
         "img" : static_url("pics/settings.png"),
         "class" : "menubardropdown",
         "menu" : options_menu}
        ]

    return render_to_string('common/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

@register.simple_tag
def quar_menu(selection, user):
    entries = [
        {"name" : "release",
         "url" : "",
         "img" : static_url("pics/release.png"),
         "label" : _("Release")},
        {"name" : "delete",
         "url" : "",
         "img" : static_url("pics/remove.png"),
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

    menu = render_to_string('common/menu.html', 
                            {"selection" : selection, "entries" : entries})
    if user.is_superuser or is_domain_admin(user):
        extraopts = [{"name" : "to", "label" : _("To")}]
    else:
        extraopts = []
    searchbar = render_to_string('common/email_searchbar.html', {
            "MEDIA_URL" : settings.MEDIA_URL,
            "extraopts" : extraopts
            })
    return menu + searchbar

from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from mailng.extensions import amavis_quarantine

register = template.Library()

@register.simple_tag
def viewm_menu(selection, mail_id, page_id, perms):
    entries = [
        {"name" : "back",
         "url" : reverse(amavis_quarantine.main.index) + "?page=%s" % page_id,
         "img" : "/static/pics/back.png",
         "label" : _("Back to list")},
        {"name" : "headers",
         "url" : reverse(amavis_quarantine.main.viewheaders, args=[mail_id]),
         "img" : "/static/pics/add.png",
         "label" : _("View full headers"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:600,y:500}}"},
        {"name" : "release",
         "url" : reverse(amavis_quarantine.main.release, args=[mail_id])
         + "?page=%s" % page_id,
         "img" : "/static/pics/release.png",
         "label" : _("Release"),
         "confirm" : _("Release this message?")},
        {"name" : "delete",
         "url" : reverse(amavis_quarantine.main.delete, args=[mail_id])
         + "?page=%s" % page_id,
         "img" : "/static/pics/remove.png",
         "label" : _("Delete"),
         "confirm" : _("Delete this message?")}
        ]

    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

@register.simple_tag
def quar_menu(selection, perms):
    entries = [
        {"name" : "release",
         "url" : "",
         "img" : "/static/pics/release.png",
         "label" : _("Release")},
        {"name" : "delete",
         "url" : "",
         "img" : "/static/pics/remove.png",
         "label" : _("Delete")},
        ]

    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from mailng.extensions import webmail
from mailng.extensions.webmail.imap_listing import IMAPheader

register = template.Library()

@register.simple_tag
def viewm_menu(selection, folder, mail_id, page_id, perms):   
    entries = [
        {"name" : "back",
         "url" : folder + "?page=%s" % page_id + "&menu=1",
         "img" : "/static/pics/back.png",
         "label" : _("Back to list")},
        ]
    
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

@register.simple_tag
def compose_menu(selection, folder, page_id, perms):
    entries = [
        {"name" : "back",
         "url" : folder + "?page=%s" % page_id + "&menu=1",
         "img" : "/static/pics/back.png",
         "label" : _("Back to list")},
        {"name" : "sendmail",
         "url" : "",
         "img" : "/static/pics/send-receive.png",
         "label" : _("Send")},
        ]
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

@register.simple_tag
def listing_menu(selection, perms):
    entries = [
        {"name" : "compose",
         "url" : reverse(webmail.main.compose),
         "img" : "/static/pics/edit.png",
         "label" : _("New message")}
        ]

    return render_to_string("main/menu.html",
                            {"selection" : selection, "entries" : entries,
                             "perms" : perms})

@register.simple_tag
def render_headers(headers):
    fields = ["Subject", "From", "To", "Cc", "Date"]
    result = []
    for f in fields:
        if not f in headers.keys():
            continue
        try:
            result += [{"name" : f, "value" : getattr(IMAPheader, "parse_%s" % f.lower())(headers[f])}]
        except AttributeError:
            result += [{"name" : f, "value" : headers[f]}]
    return render_to_string("webmail/headers.html", {
            "headers" : result
            })
    

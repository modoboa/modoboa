from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from mailng.extensions import webmail
from mailng.extensions.webmail.imap_listing import IMAPheader

register = template.Library()

def backurl(session, **kwargs):
    res = session["folder"]
    params = ""
    for key in ["page"]:
        if key in session.keys():
            if params != "":
                params += "&"
            params += "%s=%s" % (key, session[key])
    for k, v in kwargs.iteritems():
        if params != "":
            params += "&"
        params += "%s=%s" % (k, v)
    if params != "":
        res += "?%s" % params
    return res

@register.simple_tag
def viewm_menu(selection, session, mail_id, perms):   
    entries = [
        {"name" : "back",
         "url" : "%s?page=%s" % (session["folder"], session["page"]),
         "img" : "/static/pics/back.png",
         "label" : _("Back")},
        {"name" : "reply",
         "url" : "reply/",
         "img" : "/static/pics/reply.png",
         "label" : _("Reply")},
        {"name" : "reply-all",
         "url" : "",
         "img" : "/static/pics/reply-all.png",
         "label" : _("Reply all")},
        {"name" : "forward",
         "url" : "",
         "img" : "/static/pics/alias.png",
         "label" : _("Forward")},
        {"name" : "delete",
         "img" : "/static/pics/remove.png",
         "url" : reverse(webmail.main.delete, args=[session["folder"], mail_id]),
         "label" : _("Delete")},
        ]
    
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

@register.simple_tag
def compose_menu(selection, session, perms):
    entries = [
        {"name" : "back",
         "url" : "%s?page=%s" % (session["folder"], session["page"]),
         "img" : "/static/pics/back.png",
         "label" : _("Back")},
        {"name" : "sendmail",
         "url" : "",
         "img" : "/static/pics/send-receive.png",
         "label" : _("Send")},
        ]
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

@register.simple_tag
def listing_menu(selection, folder, perms):
    entries = [
        {"name" : "compose",
         "url" : reverse(webmail.main.compose),
         "img" : "/static/pics/edit.png",
         "label" : _("New message")},
        ]
    if folder in ["Trash"]:
        entries += [
            {"name" : "empty",
             "url" : reverse(webmail.main.empty, args=[folder]),
             "img" : "/static/pics/clear.png",
             "label" : _("Empty trash")}
            ]

    return render_to_string("main/menu.html",
                            {"selection" : selection, "entries" : entries,
                             "perms" : perms})

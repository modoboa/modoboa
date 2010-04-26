from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from mailng.extensions import webmail
from mailng.extensions.webmail.imap_listing import IMAPheader

register = template.Library()

@register.simple_tag
def viewm_menu(selection, backurl, folder, mail_id, perms):   
    entries = [
        {"name" : "back",
         "url" : backurl,
         "img" : "/static/pics/back.png",
         "label" : _("Back")},
        {"name" : "reply",
         "url" : "reply/",
         "img" : "/static/pics/reply.png",
         "label" : _("Reply")},
        {"name" : "replyall",
         "url" : "reply/",
         "img" : "/static/pics/reply-all.png",
         "label" : _("Reply all")},
        {"name" : "forward",
         "url" : "forward/",
         "img" : "/static/pics/alias.png",
         "label" : _("Forward")},
        {"name" : "delete",
         "img" : "/static/pics/remove.png",
         "url" : reverse(webmail.main.delete, args=[folder, mail_id]),
         "label" : _("Delete")},
        ]
    
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

@register.simple_tag
def compose_menu(selection, backurl, perms):
    entries = [
        {"name" : "back",
         "url" : backurl,
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
        {"name" : "actions",
         "img" : "/static/pics/domains.png",
         "label" : _("Mark messages"),
         "class" : "menubardropdown",
         "menu" : [
                {"name" : "mark-read",
                 "label" : _("As read")},
                {"name" : "mark-unread",
                 "label" : _("As unread")}
                ]
         }
        ]
    if folder in ["Trash"]:
        entries += [
            {"name" : "empty",
             "url" : reverse(webmail.main.empty, args=[folder]),
             "img" : "/static/pics/clear.png",
             "label" : _("Empty trash")}
            ]
    menu = render_to_string("main/menu.html",
                            {"selection" : selection, "entries" : entries,
                             "perms" : perms})
    searchbar = render_to_string("common/email_searchbar.html", {})
    return menu + searchbar

@register.simple_tag
def print_folders(folders):
    result = ""
    for fd in folders:
        if fd.has_key("icon"):
            icon = fd["icon"]
        else:
            icon = "folder.png"
        result += "<li class='droppable'>\n"
        result += "<a href='%s' name='loadfolder'>%s</a>\n" \
            % (fd.has_key("path") and fd["path"] or fd["name"], fd["name"])
        if fd.has_key("sub"):
            result += "<img name='%s' class='clickable' src='/static/pics/%s' />\n" \
                % (fd["path"], icon)
            result += "<ul name='%s' class='hidden'>" % (fd["path"]) + print_folders(fd["sub"]) + "</ul>\n"
        else:
            result += "<img src='/static/pics/%s' />\n" % icon
        result += "</li>\n"
    return result

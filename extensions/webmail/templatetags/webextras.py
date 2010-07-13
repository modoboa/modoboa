from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.extensions import webmail
from modoboa.extensions.webmail.lib import IMAPheader
from modoboa.lib import parameters

register = template.Library()

@register.simple_tag
def viewm_menu(selection, backurl, folder, mail_id, user):   
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
         "url" : reverse(webmail.views.delete, args=[folder, mail_id]),
         "label" : _("Delete")},
        ]
    
    return render_to_string('common/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "user" : user})

@register.simple_tag
def compose_menu(selection, backurl, user):
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
    return render_to_string('common/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "user" : user})

@register.simple_tag
def listing_menu(selection, folder, user):
    entries = [
        {"name" : "compose",
         "url" : reverse(webmail.views.compose),
         "img" : "/static/pics/edit.png",
         "label" : _("New message")},
        {"name" : "mark",
         "img" : "/static/pics/domains.png",
         "label" : _("Mark messages"),
         "class" : "menubardropdown",
         "menu" : [
                {"name" : "mark-read",
                 "label" : _("As read"),
                 "url" : reverse(webmail.views.mark, args=[folder]) + "?status=read"},
                {"name" : "mark-unread",
                 "label" : _("As unread"),
                 "url" : reverse(webmail.views.mark, args=[folder]) + "?status=unread"}
                ]
         },
        {"name" : "actions",
         "img" : "/static/pics/settings.png",
         "label" : _("Actions"),
         "class" : "menubardropdown",
         "width" : "150",
         "menu" : [
                {"name" : "fdaction",
                 "label" : _("Compress folder"),
                 "img" : "/static/pics/compress.png",
                 "url" : "compact/%s/" % folder},
                {"name" : "fdaction",
                 "label" : _("Empty folder"),
                 "img" : "/static/pics/clear.png",
                 "url" : folder == parameters.get_user(user, "webmail", 
                                                       "TRASH_FOLDER") \
                     and reverse(webmail.views.empty, args=[folder]) or ""}
                ]
         }
        ]
    menu = render_to_string("common/menu.html",
                            {"selection" : selection, "entries" : entries,
                             "user" : user})
    searchbar = render_to_string("common/email_searchbar.html", {})
    return menu + searchbar

@register.simple_tag
def print_folders(folders):
    result = ""
    for fd in folders:
        if fd.has_key("class"):
            cssclass = fd["class"]
        else:
            cssclass = "folder"
        name = ""
        if fd.has_key("sub"):
            cssclass += " clickable"
            name = fd["path"]
        result += "<li name='%s' class='droppable %s'>\n" % (name, cssclass)
        label = fd["name"]
        cssclass = ""
        if fd.has_key("unseen"):
            label += " (%d)" % fd["unseen"]
            cssclass = "unseen"
        result += "<a href='%s' class='%s' name='loadfolder'>%s</a>\n" \
            % (fd.has_key("path") and fd["path"] or fd["name"], cssclass, label)
        if fd.has_key("sub"):
            result += "<ul name='%s' class='hidden'>" % (fd["path"]) + print_folders(fd["sub"]) + "</ul>\n"
        result += "</li>\n"
    return result

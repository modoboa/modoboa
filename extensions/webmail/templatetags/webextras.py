from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf import settings
from modoboa.extensions import webmail
from modoboa.extensions.webmail.lib import IMAPheader
from modoboa.lib import parameters, static_url

register = template.Library()

@register.simple_tag
def viewm_menu(selection, backurl, folder, mail_id, user):   
    entries = [
        {"name" : "back",
         "url" : backurl,
         "img" : static_url("pics/back.png"),
         "label" : _("Back")},
        {"name" : "reply",
         "url" : "reply/",
         "img" : static_url("pics/reply.png"),
         "label" : _("Reply")},
        {"name" : "replyall",
         "url" : "reply/",
         "img" : static_url("pics/reply-all.png"),
         "label" : _("Reply all")},
        {"name" : "forward",
         "url" : "forward/",
         "img" : static_url("pics/alias.png"),
         "label" : _("Forward")},
        {"name" : "delete",
         "img" : static_url("pics/remove.png"),
         "url" : reverse(webmail.views.delete, args=[folder, mail_id]),
         "label" : _("Delete")},
        {"name" : "display_options",
         "label" : _("Display options"),
         "img" : static_url("pics/settings.png"),
         "class" : "menubardropdown",
         "menu" : [
                 {"name" : "activate_links", 
                  "label" : _("Activate links"),
                  "url" : reverse(webmail.views.viewmail, args=[folder, mail_id]) + "?links=1"},
                 {"name" : "disable_links", 
                  "label" : _("Disable links"),
                  "url" : reverse(webmail.views.viewmail, args=[folder, mail_id]) + "?links=0"},
                ]
         }
        ]
    
    return render_to_string('common/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "user" : user})

@register.simple_tag
def compose_menu(selection, backurl, user):
    entries = [
        {"name" : "back",
         "url" : backurl,
         "img" : static_url("pics/back.png"),
         "label" : _("Back")},
        {"name" : "sendmail",
         "url" : "",
         "img" : static_url("pics/send-receive.png"),
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
         "img" : static_url("pics/edit.png"),
         "label" : _("New message")},
        {"name" : "mark",
         "img" : static_url("pics/domains.png"),
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
         "img" : static_url("pics/settings.png"),
         "label" : _("Actions"),
         "class" : "menubardropdown",
         "width" : "150",
         "menu" : [
                {"name" : "fdaction",
                 "label" : _("Compress folder"),
                 "img" : static_url("pics/compress.png"),
                 "url" : "compact/%s/" % folder},
                ]
         }
        ]
    if folder == parameters.get_user(user, "TRASH_FOLDER"):
        entries[2]["menu"] += [
            {"name" : "fdaction",
             "label" : _("Empty folder"),
             "img" : static_url("pics/clear.png"),
             "url" : reverse(webmail.views.empty, args=[folder])}
            ]
    menu = render_to_string("common/menu.html",
                            {"selection" : selection, "entries" : entries,
                             "user" : user})
    searchbar = render_to_string("common/email_searchbar.html", {
            "MEDIA_URL" : settings.MEDIA_URL
            })
    return menu + searchbar

@register.simple_tag
def print_folders(folders, selected=None, withunseen=False, withmenu=False):
    result = ""

    import pprint
    pprint.PrettyPrinter(indent=2).pprint(folders)
    print "END"


    for fd in folders:
        if fd.has_key("class"):
            cssclass = fd["class"]
        else:
            cssclass = "folder"
        name = ""
        if fd.has_key("sub"):
            cssclass += " clickable"
            name = fd["path"]
        label = fd["name"]
        if selected == label:
            cssclass += " selected"
        result += "<li name='%s' class='droppable %s'>\n" % (name, cssclass)
        if withmenu:
            result += "<img src='%spics/go-down.png' class='footer' />" % settings.MEDIA_URL

        cssclass = ""
        if withunseen and fd.has_key("unseen"):
            label += " (%d)" % fd["unseen"]
            cssclass = "unseen"
        result += "<a href='%s' class='%s' name='loadfolder'>%s</a>\n" \
            % (fd.has_key("path") and fd["path"] or fd["name"], cssclass, label)
        if fd.has_key("sub") and len(fd["sub"]):
            result += "<ul name='%s' class='hidden'>" % (fd["path"]) + print_folders(fd["sub"], selected) + "</ul>\n"
        result += "</li>\n"
    return result

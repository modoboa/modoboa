# coding: utf-8
from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf import settings

from modoboa.extensions.webmail.lib import (
    imapheader, separate_mailbox
)
from modoboa.lib import parameters

register = template.Library()


@register.simple_tag
def viewmail_menu(selection, folder, user, mail_id=None):
    """Menu of the viewmail location."""
    entries = [
        {"name": "back",
         "url": "javascript:history.go(-1)",
         "img": "fa fa-arrow-left",
         "class": "btn-default",
         "label": _("Back")},
        {"name": "reply",
         "url": "action=reply&mbox=%s&mailid=%s" % (folder, mail_id),
         "img": "fa fa-mail-reply",
         "class": "btn-primary",
         "label": _("Reply"),
         "menu": [
             {"name": "replyall",
              "url": "action=reply&mbox=%s&mailid=%s&all=1" % (folder, mail_id),
              "img": "fa fa-mail-reply-all",
              "label": _("Reply all")},
             {"name": "forward",
              "url": "action=forward&mbox=%s&mailid=%s" % (folder, mail_id),
              "img": "fa fa-mail-forward",
              "label": _("Forward")},
        ]},
        {"name": "delete",
         "img": "fa fa-trash",
         "class": "btn-danger",
         "url": "{0}?mbox={1}&selection[]={2}".format(
             reverse("webmail:mail_delete"), folder, mail_id),
         "title": _("Delete")
        },
        {"name": "display_options",
         "title": _("Display options"),
         "img": "fa fa-cog",
         "menu": [
             {"name": "activate_links",
              "label": _("Activate links")},
             {"name": "disable_links",
              "label": _("Disable links")}
         ]
         }
    ]
    menu = render_to_string('common/buttons_list.html',
                            {"selection": selection, "entries": entries,
                             "user": user, "extraclasses": "pull-left"})

    return menu


@register.simple_tag
def compose_menu(selection, backurl, user, **kwargs):
    """The menu of the compose action."""
    entries = [
        {"name": "back",
         "url": "javascript:history.go(-2);",
         "img": "fa fa-arrow-left",
         "class": "btn-default",
         "label": _("Back")},
        {"name": "sendmail",
         "url": "",
         "img": "fa fa-send",
         "class": "btn-default btn-primary",
         "label": _("Send")},
    ]
    context = {
        "selection": selection, "entries": entries, "user": user
    }
    context.update(kwargs)
    return render_to_string('webmail/compose_menubar.html', context)


@register.simple_tag
def listmailbox_menu(selection, folder, user):
    """The menu of the listmailbox action."""
    entries = [
        {"name": "totrash",
         "title": _("Delete"),
         "class": "btn-danger",
         "img": "fa fa-trash",
         "url": reverse("webmail:mail_delete")
         },
        {"name": "actions",
         "label": _("Actions"),
         "class": "btn btn-default",
         "menu": [
             {"name": "mark-read",
              "label": _("Mark as read"),
              "url": "{0}?status=read".format(
                  reverse("webmail:mail_mark", args=[folder]))},
             {"name": "mark-unread",
              "label": _("Mark as unread"),
              "url": "{0}?status=unread".format(
                  reverse("webmail:mail_mark", args=[folder]))},
         ]
         },
    ]
    if folder == parameters.get_user(user, "TRASH_FOLDER"):
        entries[0]["class"] += " disabled"
        entries[1]["menu"] += [
            {"name": "empty",
             "label": _("Empty folder"),
             "url": "{0}?name={1}".format(
                 reverse("webmail:trash_empty"), folder)}
        ]
    return render_to_string('webmail/main_action_bar.html', {
        'selection': selection, 'entries': entries, 'user': user, 'css': "nav",
        'STATIC_URL': settings.STATIC_URL
    })


@register.simple_tag
def print_mailboxes(
        tree, selected=None, withunseen=False, selectonly=False,
        hdelimiter='.'):
    """Display a tree of mailboxes and sub-mailboxes.

    :param tree: the mailboxes to display
    """
    result = ""

    for mbox in tree:
        cssclass = ""
        name = mbox["path"] if "sub" in mbox else mbox["name"]
        label = separate_mailbox(mbox["name"], hdelimiter)[0]
        if mbox.get("removed", False):
            cssclass = "disabled"
        elif selected == name:
            cssclass = "active"
        result += "<li name='%s' class='droppable %s'>\n" % (name, cssclass)
        cssclass = ""
        extra_attrs = ""
        if withunseen and "unseen" in mbox:
            label += " (%d)" % mbox["unseen"]
            cssclass += " unseen"
            extra_attrs = ' data-toggle="%d"' % mbox["unseen"]

        if "sub" in mbox:
            if selected is not None and selected != name and selected.count(name):
                ul_state = "visible"
                div_state = "expanded"
            else:
                ul_state = "hidden"
                div_state = "collapsed"
            result += "<div class='clickbox %s'></div>" % div_state

        result += "<a href='%s' class='%s' name='%s'%s>" % (
            "path" in mbox and mbox["path"] or mbox["name"], cssclass,
            'selectfolder' if selectonly else 'loadfolder', extra_attrs
        )

        iclass = mbox["class"] if "class" in mbox \
            else "fa fa-folder"
        result += "<span class='%s'></span> %s</a>" % (iclass, label)

        if "sub" in mbox and mbox["sub"]:
            result += "<ul name='%s' class='nav nav-pills nav-stacked %s'>" % (
                mbox["path"], ul_state) + print_mailboxes(
                    mbox["sub"], selected, withunseen, selectonly, hdelimiter
                ) + "</ul>\n"
        result += "</li>\n"
    return result


@register.simple_tag
def mboxes_menu():
    """Mailboxes menu."""
    entries = [
        {"name": "newmbox",
         "url": reverse("webmail:folder_add"),
         "img": "fa fa-plus",
         "label": _("Create a new mailbox"),
         "modal": True,
         "modalcb": "webmail.mboxform_cb",
         "closecb": "webmail.mboxform_close",
         "class": "btn-default btn-xs"},
        {"name": "editmbox",
         "url": reverse("webmail:folder_change"),
         "img": "fa fa-edit",
         "label": _("Edit the selected mailbox"),
         "class": "btn-default btn-xs"},
        {"name": "removembox",
         "url": reverse("webmail:folder_delete"),
         "img": "fa fa-trash",
         "label": _("Remove the selected mailbox"),
         "class": "btn-default btn-xs"},
        {"name": "compress",
         "img": "fa fa-compress",
         "label": _("Compress folder"),
         "class": "btn-default btn-xs",
         "url": reverse("webmail:folder_compress")}
    ]

    return render_to_string('common/menu.html', dict(
        entries=entries, css="dropdown-menu"
    ))


@register.filter
def parse_imap_header(value, header):
    """Simple template tag to display a IMAP header."""
    try:
        value = getattr(imapheader, "parse_%s" % header)(value)
    except AttributeError:
        pass
    return value

# coding: utf-8
from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf import settings
from modoboa.extensions import webmail
from modoboa.extensions.webmail.lib import separate_mailbox
from modoboa.lib import parameters

register = template.Library()


@register.simple_tag
def viewmail_menu(selection, folder, user, mail_id=None):
    entries = [
        {"name": "back",
             "url": "javascript:history.go(-2);",
             "img": "glyphicon glyphicon-arrow-left",
             "class": "btn-primary",
             "label": _("Back")},
        {"name": "reply",
         "url": "action=reply&mbox=%s&mailid=%s" % (folder, mail_id),
         "img": "glyphicon glyphicon-share",
         "class": "btn-default",
         "label": _("Reply")},
        {"name": "replyall",
         "url": "action=reply&mbox=%s&mailid=%s&all=1" % (folder, mail_id),
         "img": "",
         "class": "btn-default",
         "label": _("Reply all")},
        {"name": "forward",
         "url": "action=forward&mbox=%s&mailid=%s" % (folder, mail_id),
         "img": "glyphicon glyphicon-arrow-right",
         "class": "btn-default",
         "label": _("Forward")},
        {"name": "delete",
         "img": "glyphicon glyphicon-trash",
         "class": "btn-default",
         "url": reverse(webmail.views.delete) + "?mbox=%s&selection[]=%s" % (folder, mail_id),
         "label": _("Delete")},
        {"name": "display_options",
         "label": _("Display options"),
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

    entries = [{"name": "close",
                "title": _("Close this message"),
                "img": "glyphicon glyphicon-remove"}]
    menu += render_to_string(
        'common/buttons_list.html',
        {"entries": entries, "extraclasses": "pull-right"}
    )
    return menu


@register.simple_tag
def compose_menu(selection, backurl, user):
    entries = [
        {"name": "back",
         "url": "javascript:history.go(-2);",
         "img": "glyphicon glyphicon-arrow-left",
         "class": "btn-primary",
         "label": _("Back")},
        {"name": "sendmail",
         "url": "",
         "img": "glyphicon glyphicon-envelope",
         "class": "btn-default",
         "label": _("Send")},
    ]
    return render_to_string('common/buttons_list.html',
                            {"selection": selection, "entries": entries,
                             "user": user})


@register.simple_tag
def listmailbox_menu(selection, folder, user):
    entries = [
        {"name": "compose",
         "url": "compose",
         "img": "glyphicon glyphicon-edit",
         "label": _("New message"),
         "class": "btn btn-default"},
        {"name": "totrash",
         "label": "",
         "class": "btn btn-default",
         "img": "glyphicon glyphicon-trash",
         "url": reverse("modoboa.extensions.webmail.views.delete"),
         },
        {"name": "mark",
         "label": _("Mark messages"),
         "class": "btn btn-default",
         "menu": [
             {"name": "mark-read",
              "label": _("As read"),
              "url": reverse(webmail.views.mark, args=[folder]) + "?status=read"},
             {"name": "mark-unread",
              "label": _("As unread"),
              "url": reverse(webmail.views.mark, args=[folder]) + "?status=unread"}
         ]
         },
        {"name": "actions",
         "label": _("Actions"),
         "class": "btn btn-default",
         "menu": [
             {"name": "compress",
              "label": _("Compress folder"),
              "url": "compact/%s/" % folder}
         ]
         },
    ]
    if folder == parameters.get_user(user, "TRASH_FOLDER"):
        entries[1]["class"] += " disabled"
        entries[3]["menu"] += [
            {"name": "empty",
             "label": _("Empty folder"),
             "url": reverse(webmail.views.empty, args=[folder])}
        ]
    return render_to_string('webmail/main_action_bar.html', {
        'selection': selection, 'entries': entries, 'user': user, 'css': "nav",
        'STATIC_URL': settings.STATIC_URL
    })


@register.simple_tag
def print_mailboxes(tree, selected=None, withunseen=False, selectonly=False, hdelimiter='.'):
    """Display a tree of mailboxes and sub-mailboxes

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
        if "sub" in mbox:
            if selected is not None and selected != name and selected.count(name):
                ul_state = "visible"
                div_state = "expanded"
            else:
                ul_state = "hidden"
                div_state = "collapsed"
            result += "<div class='clickbox %s'></div>" % div_state

        cssclass = "block"
        extra_attrs = ""
        if withunseen and "unseen" in mbox:
            label += " (%d)" % mbox["unseen"]
            cssclass += " unseen"
            extra_attrs = ' data-toggle="%d"' % mbox["unseen"]
        iclass = mbox["class"] if "class" in mbox else "glyphicon glyphicon-folder-close"
        result += """<a href='%s' class='%s' name='%s'%s>
  <i class="%s"></i>
  %s
</a>
""" % ("path" in mbox and mbox["path"] or mbox["name"], cssclass,
       'selectfolder' if selectonly else 'loadfolder',
       extra_attrs, iclass, label)

        if "sub" in mbox and len(mbox["sub"]):
            result += "<ul name='%s' class='nav nav-list %s'>" % (mbox["path"], ul_state) \
                + print_mailboxes(mbox["sub"], selected, withunseen, selectonly, hdelimiter) + "</ul>\n"
        result += "</li>\n"
    return result

@register.simple_tag
def mboxes_menu():
    entries = [
        {"name": "newmbox",
         "url": reverse(webmail.views.newfolder),
         "img": "glyphicon glyphicon-plus",
         "title": _("Create a new mailbox"),
         "modal": True,
         "modalcb": "webmail.mboxform_cb",
         "closecb": "webmail.mboxform_close",
         "class": "btn-default btn-sm"},
        {"name": "editmbox",
         "url": reverse(webmail.views.editfolder),
         "img": "glyphicon glyphicon-edit",
         "title": _("Edit the selected mailbox"),
         "class": "btn-default btn-sm"},
        {"name": "removembox",
         "url": reverse(webmail.views.delfolder),
         "img": "glyphicon glyphicon-remove",
         "title": _("Remove the selected mailbox"),
         "class": "btn-default btn-sm"}
    ]

    return render_to_string('common/buttons_list.html', dict(
        entries=entries, css="nav"
    ))

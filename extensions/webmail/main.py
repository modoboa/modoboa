# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import include
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url

def init():
    events.register("UserMenuDisplay", menu)
    events.register("UserLogout", userlogout)
    
    parameters.register_admin("IMAP_SERVER", type="string", 
                              deflt="127.0.0.1",
                              help=_("Address of your IMAP server"))
    parameters.register_admin("IMAP_SECURED", type="list_yesno", 
                              deflt="no",
                              help=_("Use a secured connection to access IMAP server"))
    parameters.register_admin("IMAP_PORT", type="int", deflt="143",
                              help=_("Listening port of your IMAP server"))
    parameters.register_admin("SMTP_SERVER", type="string", 
                              deflt="127.0.0.1",
                              help=_("Address of your SMTP server"))
    parameters.register_admin("SMTP_SECURED_MODE", type="list", 
                              values=[("none", _("None")), 
                                      ("starttls", "STARTTLS"),
                                      ("ssl", "SSL/TLS")],
                              deflt="none",
                              help=_("Use a secured connection to access SMTP server"))
    parameters.register_admin("SMTP_PORT", type="int", deflt="25",
                              help=_("Listening port of your SMTP server"))
    parameters.register_admin("SMTP_AUTHENTICATION", type="list_yesno",
                              deflt="no",
                              help=_("Server needs authentication"))
    parameters.register_admin("MAX_ATTACHMENT_SIZE", type="int", deflt=2048,
                              help=_("Maximum attachment size in KB"))
   

    parameters.register_user("MESSAGES_PER_PAGE", type="int", deflt=40,
                             label=_("Number of displayed emails per page"),
                             help=_("Sets the maximum number of messages displayed in a page"))
    parameters.register_user("REFRESH_INTERVAL", type="int", deflt=300,
                             label=_("Listing refresh rate"),
                             help=_("Automatic folder refresh rate (in seconds)"))
    parameters.register_user("TRASH_FOLDER", type="string", deflt="Trash",
                             label=_("Trash folder"),
                             help=_("Folder where deleted messages go"))
    parameters.register_user("SENT_FOLDER", type="string", deflt="Sent",
                             label=_("Sent folder"),
                             help=_("Folder where copies of sent messages go"))
    parameters.register_user("DRAFTS_FOLDER", type="string", deflt="Drafts",
                             label=_("Drafts folder"),
                             help=_("Folder where drafts go"))
    parameters.register_user("SIGNATURE", type="text", deflt="",
                             label=_("Signature text"),
                             help=_("User defined email signature"))
    parameters.register_user("EDITOR", type="list", deflt="plain",
                             label=_("Default editor"),
                             values=[("html", "html"), ("plain", "text")],
                             help=_("The default editor to use when composing a message"))
    parameters.register_user("DISPLAYMODE", type="list", deflt="plain",
                             label=_("Default message display mode"),
                             values=[("html", "html"), ("plain", "text")],
                             help=_("The default mode used when displaying a message"))
    parameters.register_user("ENABLE_LINKS", type="list_yesno", deflt="no",
                             label=_("Enable HTML links display"),
                             help=_("Enable/Disable HTML links display"))

def destroy():
    events.unregister("UserMenuDisplay", menu)
    parameters.unregister_app("webmail")

def infos():
    return {
        "name" : "Webmail",
        "version" : "1.0",
        "description" : _("Simple IMAP webmail")
        }

def urls(prefix):
    return (r'^%swebmail/' % prefix,
            include('modoboa.extensions.webmail.urls'))

def menu(**kwargs):
    import views

    if kwargs["target"] != "top_menu":
        return []
    return [
        {"name" : "webmail",
         "label" : _("Webmail"),
         "url" : reverse(views.index),
         "img" : static_url("pics/webmail.png")}
        ]

def userlogout(**kwargs):
    from lib import IMAPconnector

    if kwargs["request"].user.id == 1:
        return
    try:
        m = IMAPconnector(user=kwargs["request"].user.username,
                          password=kwargs["request"].session["password"])
    except Exception, e:
        pass
    else:
        m.logout()

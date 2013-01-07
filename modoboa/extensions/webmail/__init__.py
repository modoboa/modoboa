# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url
from modoboa.extensions import ModoExtension, exts_pool

class Webmail(ModoExtension):
    name = "webmail"
    label = "Webmail"
    version = "1.0"
    description = ugettext_lazy("Simple IMAP webmail")
    needs_media = True
    
    def load(self):
        parameters.register_app(uparams_opts=dict(needs_mailbox=True))
        
        parameters.register_admin("IMAP_SERVER", type="string", 
                                  deflt="127.0.0.1",
                                  help=ugettext_lazy("Address of your IMAP server"))
        parameters.register_admin("IMAP_SECURED", type="list_yesno", 
                                  deflt="no",
                                  help=ugettext_lazy("Use a secured connection to access IMAP server"))
        parameters.register_admin("IMAP_PORT", type="int", deflt="143",
                                  help=ugettext_lazy("Listening port of your IMAP server"))
        parameters.register_admin("SMTP_SERVER", type="string", 
                                  deflt="127.0.0.1",
                                  help=ugettext_lazy("Address of your SMTP server"))
        parameters.register_admin("SMTP_SECURED_MODE", type="list", 
                                  values=[("none", ugettext_lazy("None")), 
                                          ("starttls", "STARTTLS"),
                                          ("ssl", "SSL/TLS")],
                                  deflt="none",
                                  help=ugettext_lazy("Use a secured connection to access SMTP server"))
        parameters.register_admin("SMTP_PORT", type="int", deflt="25",
                                  help=ugettext_lazy("Listening port of your SMTP server"))
        parameters.register_admin("SMTP_AUTHENTICATION", type="list_yesno",
                                  deflt="no",
                                  help=ugettext_lazy("Server needs authentication"))
        parameters.register_admin("MAX_ATTACHMENT_SIZE", type="int", deflt=2048,
                                  help=ugettext_lazy("Maximum attachment size in bytes (or KB, MB, GB if specified)"))
        
        parameters.register_user("MESSAGES_PER_PAGE", type="int", deflt=40,
                                 label=ugettext_lazy("Number of displayed emails per page"),
                                 help=ugettext_lazy("Sets the maximum number of messages displayed in a page"))
        parameters.register_user("REFRESH_INTERVAL", type="int", deflt=300,
                                 label=ugettext_lazy("Listing refresh rate"),
                                 help=ugettext_lazy("Automatic folder refresh rate (in seconds)"))
        parameters.register_user("TRASH_FOLDER", type="string", deflt="Trash",
                                 label=ugettext_lazy("Trash folder"),
                                 help=ugettext_lazy("Folder where deleted messages go"))
        parameters.register_user("SENT_FOLDER", type="string", deflt="Sent",
                                 label=ugettext_lazy("Sent folder"),
                                 help=ugettext_lazy("Folder where copies of sent messages go"))
        parameters.register_user("DRAFTS_FOLDER", type="string", deflt="Drafts",
                                 label=ugettext_lazy("Drafts folder"),
                                 help=ugettext_lazy("Folder where drafts go"))
        parameters.register_user("SIGNATURE", type="text", deflt="",
                                 label=ugettext_lazy("Signature text"),
                                 help=ugettext_lazy("User defined email signature"))
        parameters.register_user("EDITOR", type="list", deflt="plain",
                                 label=ugettext_lazy("Default editor"),
                                 values=[("html", "html"), ("plain", "text")],
                                 help=ugettext_lazy("The default editor to use when composing a message"))
        parameters.register_user("DISPLAYMODE", type="list", deflt="plain",
                                 label=ugettext_lazy("Default message display mode"),
                                 values=[("html", "html"), ("plain", "text")],
                                 help=ugettext_lazy("The default mode used when displaying a message"))
        parameters.register_user("ENABLE_LINKS", type="list_yesno", deflt="no",
                                 label=ugettext_lazy("Enable HTML links display"),
                                 visible_if="DISPLAYMODE=html",
                                 help=ugettext_lazy("Enable/Disable HTML links display"))

    def destroy(self):
        events.unregister("UserMenuDisplay", menu)
        parameters.unregister_app("webmail")

exts_pool.register_extension(Webmail)

@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "top_menu":
        return []
    if not user.has_mailbox:
        return []
    return [
        {"name" : "webmail",
         "label" : _("Webmail"),
         "url" : reverse("modoboa.extensions.webmail.views.index")},
        ]

@events.observe("UserLogout")
def userlogout(request):
    from lib import IMAPconnector
    from exceptions import ImapError

    if not request.user.has_mailbox:
        return
    try:
        m = IMAPconnector(user=request.user.username,
                          password=request.session["password"])
    except Exception, e:
        return
    
    # The following statement may fail under Python 2.6...
    try:
        m.logout()
    except ImapError:
        pass

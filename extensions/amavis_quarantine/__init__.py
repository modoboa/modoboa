# coding: utf-8
"""
Amavis quarantine manager (SQL based)


"""
from django.utils.translation import ugettext_noop as _, ugettext
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters

baseurl = "quarantine"

def infos():
    return {
        "name" : "Amavis quarantine",
        "version" : "1.0",
        "description" : ugettext("Simple amavis quarantine management tool"),
        "url" : "quarantine"
        }

def load():
    parameters.register_admin(
        "MAX_MESSAGES_AGE", type="int", 
        deflt=14,
        help=_("Quarantine messages maximum age (in days) before deletion")
        )
    parameters.register_admin(
        "RELEASED_MSGS_CLEANUP", type="list_yesno", deflt="no",
        help=_("Remove messages marked as released while cleaning up the database")
        )
    parameters.register_admin("AM_PDP_MODE", type="list", 
                              deflt="unix",
                              values=[("inet", "inet"), ("unix", "unix")],
                              help=_("Mode used to access the PDP server"))
    parameters.register_admin("AM_PDP_HOST", type="string", 
                              deflt="localhost", 
                              help=_("PDP server address (if inet mode)"))
    parameters.register_admin("AM_PDP_PORT", type="int", 
                              deflt=9998, 
                              help=_("PDP server port (if inet mode)"))
    parameters.register_admin("AM_PDP_SOCKET", type="string", 
                              deflt=_("/var/amavis/amavisd.sock"),
                              help=_("Path to the PDP server socket (if unix mode)"))

    parameters.register_user(
        "MESSAGES_PER_PAGE", type="int", deflt=40,
        label="Number of displayed emails per page",
        help=_("Sets the maximum number of messages displayed in a page")
        )

def destroy():
    events.unregister("UserMenuDisplay", menu)
    parameters.unregister_app("amavis_quarantine")

@events.observe("UserMenuDisplay")
def menu(target, user):
    from modoboa.lib.webutils import static_url

    if target == "top_menu":
        return [
            {"name" : "quarantine",
             "label" : _("Quarantine"),
             "url" : reverse('modoboa.extensions.amavis_quarantine.views.index'),
             "img" : static_url("pics/quarantine.png")}
            ]
    return []


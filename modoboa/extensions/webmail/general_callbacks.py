from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.lib import events


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "top_menu":
        return []
    if not user.mailbox_set.count():
        return []
    return [
        {"name": "webmail",
         "label": _("Webmail"),
         "url": reverse("webmail:index")},
    ]


@events.observe("UserLogout")
def userlogout(request):
    from .lib import IMAPconnector
    from .exceptions import ImapError

    if not request.user.mailbox_set.count():
        return
    try:
        m = IMAPconnector(user=request.user.username,
                          password=request.session["password"])
    except Exception:
        # TODO silent exception are bad : we should at least log it
        return

    # The following statement may fail under Python 2.6...
    try:
        m.logout()
    except ImapError:
        pass

# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool


class Webmail(ModoExtension):
    name = "webmail"
    label = "Webmail"
    version = "1.0"
    description = ugettext_lazy("Simple IMAP webmail")
    needs_media = True

    def load(self):
        from .app_settings import ParametersForm, UserSettings

        parameters.register(ParametersForm, "Webmail")
        parameters.register(UserSettings, "Webmail")

    def destroy(self):
        events.unregister("UserMenuDisplay", menu)
        parameters.unregister()

exts_pool.register_extension(Webmail)


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "top_menu":
        return []
    if not user.mailbox_set.count():
        return []
    return [
        {"name": "webmail",
         "label": _("Webmail"),
         "url": reverse("modoboa.extensions.webmail.views.index")},
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

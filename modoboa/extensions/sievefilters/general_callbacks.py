from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.lib import events


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "options_menu":
        return []
    if not user.mailbox_set.count():
        return []
    return [
        {"name": "sievefilters",
         "label": _("Message filters"),
         "url": reverse("sievefilters:index"),
         "img": "fa fa-filter"}
    ]


@events.observe("UserLogout")
def userlogout(request):
    from .lib import SieveClient

    if not request.user.mailbox_set.count():
        return
    try:
        sc = SieveClient(user=request.user.username,
                         password=request.session["password"])
    except Exception:
        pass
    else:
        sc.logout()

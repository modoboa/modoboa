from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf import settings
from modoboa.lib.webutils import _render_to_string

register = template.Library()


@register.simple_tag
def viewm_menu(mail_id, rcpt):
    entries = [
        {"name": "release",
         "img": "icon-white icon-ok",
         "class": "btn-success",
         "url": reverse('modoboa.extensions.amavis.views.release', args=[mail_id])
         + ("?rcpt=%s" % rcpt if rcpt else ""),
         "label": _("Release")},
        {"name": "delete",
         "class": "btn-danger",
         "img": "icon-white icon-trash",
         "url": reverse('modoboa.extensions.amavis.views.delete', args=[mail_id])
         + ("?rcpt=%s" % rcpt if rcpt else ""),
         "label": _("Delete")},
        {"name": "headers",
         "url": reverse('modoboa.extensions.amavis.views.viewheaders', args=[mail_id]),
         "label": _("View full headers")},
    ]

    menu = render_to_string('common/buttons_list.html',
                            {"entries": entries, "extraclasses": "pull-left"})

    entries = [{"name": "close",
                "url": "javascript:history.go(-1);",
                "img": "icon-remove"}]
    menu += render_to_string(
        'common/buttons_list.html',
        {"entries": entries, "extraclasses": "pull-right"}
    )

    return menu


@register.simple_tag
def viewm_menu_simple(user, mail_id, rcpt, secret_id=""):
    entries = [
        {"name": "release",
         "img": "icon-white icon-ok",
         "class": "btn-success",
         "url": reverse('modoboa.extensions.amavis.views.release', args=[mail_id]) \
             + ("?rcpt=%s" % rcpt \
                    + (("&secret_id=%s" % secret_id) if secret_id != "" else "")),
         "label": _("Release")},
        {"name": "delete",
         "img": "icon-white icon-trash",
         "class": "btn-danger",
         "url": reverse('modoboa.extensions.amavis.views.delete', args=[mail_id]) \
             + "?rcpt=%s" % rcpt \
             + ("&secret_id=%s" % secret_id if secret_id != "" else ""),
         "label": _("Delete")},
    ]

    return render_to_string('common/buttons_list.html',
                            {"entries": entries})


@register.simple_tag
def quar_menu():
    """Render the quarantine listing menu.

    :rtype: str
    :return: resulting HTML
    """
    extraopts = [{"name": "to", "label": _("To")}]
    return render_to_string('amavis/main_action_bar.html', {
        'extraopts': extraopts
    })

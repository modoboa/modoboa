import re
from django import template
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.sessions.models import Session
from modoboa.lib import events


register = template.Library()


@register.simple_tag
def core_menu(selection, user):
    entries = \
        events.raiseQueryEvent("AdminMenuDisplay", "top_menu", user)
    if user.is_superuser:
        entries += [
            {"name": "settings",
             "label": _("Modoboa"),
             "url": reverse("modoboa.core.views.admin.viewsettings")}
        ]

    if not len(entries):
        return ""
    return render_to_string("common/menulist.html", {
        "entries": entries,
        "selection": selection,
        "user": user}
    )


@register.simple_tag
def settings_menu(selection, user):
    entries = [
        {"name": "extensions",
         "class": "ajaxlink",
         "url": "extensions/",
         "label": _("Extensions"),
         "img": ""},
        {"name": "info",
         "class": "ajaxlink",
         "url": "info/",
         "label": _("Information")},
        {"name": "logs",
         "class": "ajaxlink",
         "url": "logs/",
         "label": _("Logs")},
        {"name": "parameters",
         "class": "ajaxlink",
         "url": "parameters/",
         "img": "",
         "label": _("Parameters")},
    ]
    return render_to_string('common/menu.html', {
        "entries": entries,
        "css": "nav nav-list",
        "selection": selection,
        "user": user
    })


@register.simple_tag
def extensions_menu(selection, user):
    menu = events.raiseQueryEvent("UserMenuDisplay", "top_menu", user)
    return render_to_string('common/menulist.html', {
        "selection": selection, "entries": menu, "user": user
    })


@register.simple_tag
def admin_menu(selection, user):
    entries = [
        {"name": "extensions",
         "class": "ajaxlink",
         "url": "extensions/",
         "label": _("Extensions"),
         "img": ""},
        {"name": "info",
         "class": "ajaxlink",
         "url": "info/",
         "label": _("Information")},
        {"name": "logs",
         "class": "ajaxlink",
         "url": "logs/",
         "label": _("Logs")},
        {"name": "parameters",
         "class": "ajaxlink",
         "url": "parameters/",
         "img": "",
         "label": _("Parameters")},
    ]
    return render_to_string('common/menu.html', {
        "entries": entries,
        "css": "nav nav-list",
        "selection": selection,
        "user": user
    })


@register.simple_tag
def user_menu(user, selection):
    entries = [
        {"name": "user",
         "img": "icon-user icon-white",
         "label": user.fullname,
         "menu": [
                {"name": "settings",
                 "img": "icon-list",
                 "label": _("Settings"),
                 "url": reverse("modoboa.core.views.user.index")}
         ]}
    ]

    entries[0]["menu"] += \
        events.raiseQueryEvent("UserMenuDisplay", "options_menu", user) \
        + [{"name": "logout",
            "url": reverse("modoboa.core.views.auth.dologout"),
            "label": _("Logout"),
            "img": "icon-off"}]

    return render_to_string("common/menulist.html", {
        "selection": selection, "entries": entries, "user": user
    })


@register.simple_tag
def uprefs_menu(selection, user):
    entries = [
        {"name": "profile",
         "class": "ajaxlink",
         "url": "profile/",
         "label": _("Profile")},
        {"name": "preferences",
         "class": "ajaxlink",
         "url": "preferences/",
         "label": _("Preferences")},
    ]
    entries += events.raiseQueryEvent("UserMenuDisplay", "uprefs_menu", user)
    entries = sorted(entries, key=lambda e: e["label"])
    return render_to_string('common/menu.html', {
        "entries": entries,
        "css": "nav nav-list",
        "selection": selection,
        "user": user
    })


@register.filter
def colorize_level(level):
    classes = {
        "INFO": "text-info",
        "WARNING": "text-warning",
        "CRITICAL": "text-error"
    }
    if not level in classes:
        return level
    return "<p class='%s'>%s</p>" % (classes[level], level)


@register.filter
def tohtml(message):
    return re.sub("'(.*?)'", "<strong>\g<1></strong>", message)


@register.simple_tag
def visirule(field):
    if not hasattr(field.form, "visirules") or not field.html_name in field.form.visirules:
        return ""
    rule = field.form.visirules[field.html_name]
    return " data-visibility-field='%s' data-visibility-value='%s' " \
        % (rule["field"], rule["value"])


@register.simple_tag
def get_version():
    import pkg_resources
    return pkg_resources.get_distribution("modoboa").version


class ConnectedUsers(template.Node):
    def __init__(self, varname):
        self.varname = varname

    def render(self, context):
        from modoboa.core.models import User

        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        uid_list = []
        # Build a list of user ids from that query
        for session in sessions:
            data = session.get_decoded()
            uid = data.get('_auth_user_id', None)
            if uid:
                uid_list.append(uid)

        # Query all logged in users based on id list
        context[self.varname] = []
        for uid in uid_list:
            try:
                context[self.varname].append(User.objects.get(pk=uid))
            except User.DoesNotExist:
                pass
        return ''


@register.tag
def connected_users(parser, token):
    try:
        tag, a, varname = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            'connected_users usage: {% connected_users as users %}'
        )
    return ConnectedUsers(varname)


@register.simple_tag
def get_modoboa_logo():
    import os
    from django.conf import settings

    try:
        logo = settings.MODOBOA_CUSTOM_LOGO
    except AttributeError:
        logo = None
    if logo is None:
        return os.path.join(settings.STATIC_URL, "css/modoboa.png")
    return logo


@register.simple_tag
def extra_head_content(user):
    tpl = Template("{% for sc in static_content %}{{ sc|safe }}{% endfor %}")
    return tpl.render(
        Context(
            dict(static_content=events.raiseQueryEvent("GetStaticContent", user))
        )
    )


@register.simple_tag
def load_optionalmenu(user):
    menu = events.raiseQueryEvent("UserMenuDisplay", "top_menu_middle", user)
    return template.loader.render_to_string(
        'common/menulist.html',
        {"entries" : menu, "user" : user}
    )


@register.simple_tag
def load_notifications(user):
    content = events.raiseQueryEvent("TopNotifications", user)
    return "".join(content)


@register.simple_tag
def display_messages(msgs):
    text = ""
    level = "info"
    for m in msgs:
        level = m.tags
        text += unicode(m) + "\\\n"

    if level == "info":
        level = "success"
        timeout = "2000"
    else:
        timeout = "undefined"

    return """
<script type="text/javascript">
    $(document).ready(function() {
        $('body').notify('%s', '%s', %s);
    });
</script>
""" % (level, text, timeout)

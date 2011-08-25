# coding: utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _
from models import *
from modoboa.lib.webutils import _render_error

def is_not_localadmin(errortpl="error"):
    def dec(f):
        def wrapped_f(request, *args, **kwargs):
            if request.user.id == 1:
                return _render_error(request, errortpl, {
                        "error" : _("Invalid action, %(user)s is a local user" \
                                        % {"user" : request.user.username})
                        })
            return f(request, *args, **kwargs)

        wrapped_f.__name__ = f.__name__
        wrapped_f.__dict__ = f.__dict__
        wrapped_f.__doc__ = f.__doc__
        wrapped_f.__module__ = f.__module__
        return wrapped_f
    return dec

def is_domain_admin(user):
    """Tell if a user is administrator for a domain of not

    Whatever the domain, we just want to know if the given user is
    declared as a domain administrator.

    :param user: a User object
    :return: True if the user is a domain administrator, False otherwise.
    """
    grp = Group.objects.get(name="DomainAdmins")
    return grp in user.groups.all()

def good_domain(f):
    """Custom permission decorator

    Check if a domain administrator is accessing the good domain.

    :param f: the original called function
    """
    def dec(request, **kwargs):
        if request.user.is_superuser:
            return f(request, **kwargs)
        mb = Mailbox.objects.get(user=request.user.id)
        access = True
        if request.GET.has_key("domid"):
            dom_id = int(request.GET["domid"])
            if dom_id != mb.domain.id:
                access = False
        else:
            q = request.GET.copy()
            q["domid"] = mb.domain.id
            request.GET = q
        if access:
            return f(request, **kwargs)

        from django.conf import settings
        path = urlquote(request.get_full_path())
        login_url = settings.LOGIN_URL
        return HttpResponseRedirect("%s?next=%s" % (login_url, path))
    return dec

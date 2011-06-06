# coding: utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group
from models import *

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

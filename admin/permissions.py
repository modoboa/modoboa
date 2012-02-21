# coding: utf-8

import datetime
from django.utils.translation import ugettext as _, ugettext_noop
from django.contrib.auth.models import Group
from modoboa.lib.webutils import _render, getctx, _render_to_string
from modoboa.lib import events
from forms import *
from models import User
from tables import SuperAdminsTable, DomainAdminsTable
from lib import grant_access_to_object, ungrant_access_to_object

class Permissions(object):
    submit_label = ugettext_noop("Add")
    formtpl = 'admin/add_permission.html'

    @staticmethod
    def is_authorized(user):
        return user.is_superuser

    def get_add_form(self, request):
        raise NotImplementedError

    def add(self, request):
        raise NotImplementedError

    def delete(self, request, selection):
        raise NotImplementedError

    def get(self, request):
        raise NotImplementedError

    def _render_form(self, request, form, instring=False):
        ctx = dict(form=form, title=self.title, submit_label=self.submit_label,
                   role=self.role)
        if instring:
            return _render_to_string(request, self.formtpl, ctx)
        return _render(request, self.formtpl, ctx)

class SuperAdminsPerms(Permissions):
    title = ugettext_noop("Add super administrator")
    role = "super_admins"
    
    def get_add_form(self, request):
        form = SuperAdminForm(request.user)
        return self._render_form(request, form)

    def add(self, request):
        form = SuperAdminForm(request.user, request.POST)
        if form.is_valid():
            user = User.objects.get(pk=request.POST["user"])
            user.is_superuser = True
            user.date_joined = datetime.datetime.now()
            events.raiseEvent("SuperAdminPromotion", user)
            user.groups.clear()
            user.save()
            return True, None

        content = self._render_form(request, form, True)
        return False, getctx("ko", content=content)
    
    def delete(self, selection):
        for s in selection:
            user = User.objects.get(pk=int(s))
            if user.username == "admin":
                continue
            user.is_superuser = False
            user.save()

    def get(self, request):
        admins = User.objects.filter(is_superuser=True)
        return SuperAdminsTable(request, admins).render()
   

class DomainAdminsPerms(Permissions):
    title = ugettext_noop("Add domain administrator")
    role = "domain_admins"
    formtpl = 'admin/add_domain_admin.html'
    
    @staticmethod
    def is_authorized(user):
        return user.has_perm("admin.view_domains")

    def get_add_form(self, request):
        form = DomainAdminForm()
        return self._render_form(request, form)

    def delete(self, selection):
        dagrp = Group.objects.get(name="DomainAdmins")
        sugrp = Group.objects.get(name="SimpleUsers")
        for uid in selection:
            u = User.objects.get(pk=uid)
            u.groups.remove(dagrp)
            u.save()
            events.raiseEvent("DomainAdminDeleted", u)
            if not len(u.mailbox_set.all()):
                ungrant_access_to_object(u)
                u.delete()
            else:
                u.groups.add(sugrp)

    def get(self, request):
        domainadmins = User.objects.filter(groups__name="DomainAdmins")
        domainadmins = filter(lambda da: request.user.is_owner(da), domainadmins)
        return DomainAdminsTable(request, domainadmins).render()

def get_perms_class(user, role):
    """Retrieves the class associated to a given role

    The provided user must have the required permission to retrieve
    this class.

    If "role" is one of those provided by the admin component, its
    class is directly returned. Otherwise, a "PermsGetClass" event is
    raised to check if one of the active plugins provide the desired
    class.

    :param user: a User object
    :param role: the role to look for
    """
    parts = role.split("_")
    cname = ""
    for p in parts:
        cname += p.capitalize()
    cname += "Perms"
    if globals().has_key(cname):
        if globals()[cname].is_authorized(user):
            return globals()[cname]
        return None
    res = events.raiseQueryEvent("PermsGetClass", role)
    if not len(res):
        return None
    return res[0]

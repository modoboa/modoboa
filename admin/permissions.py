# coding: utf-8

import datetime
from django.utils.translation import ugettext as _, ugettext_noop
from django.contrib.auth.models import User, Group
from modoboa.lib.webutils import _render, getctx, _render_to_string
from modoboa.lib import events
from forms import *
from tables import SuperAdminsTable, DomainAdminsTable
from lib import set_object_ownership

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
            user.groups.clear()
            user.save()
            return True, None

        content = self._render_form(request, form, True)
        return False, getctx("ko", content=content)
    
    def delete(self, selection):
        for s in selection:
            user = User.objects.get(pk=int(s))
            if user.username == "admin":
                #messages.error(request, _("admin is intouchable!!"), fail_silently=True)
                continue
            user.is_superuser = False
            user.save()

    def get(self, request):
        admins = User.objects.filter(is_superuser=True)
        admins_list = []
        for admin in admins:
            admins_list += [{"id" : admin.id, "user_name" : admin.username,
                             "full_name" : "%s %s" % (admin.first_name, admin.last_name),
                             "date_joined" : admin.date_joined,
                             "enabled" : admin.is_active}]
        return SuperAdminsTable(request, admins_list).render()
   

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
    
    def add(self, request):
        form = DomainAdminForm(request.POST)
        if request.POST.get("user", "") != "":
            mboxid = request.POST['user']
            mb = Mailbox.objects.get(pk=mboxid)
            form.fields["user"].choices = [(mboxid, mb),]
        if form.is_valid():
            mb.user.is_superuser = False
            mb.user.date_joined = datetime.datetime.now()
            mb.user.groups.add(Group.objects.get(name="DomainAdmins"))
            mb.user.save()
            set_object_ownership(mb.user, mb.domain)
            return True, None
        content = self._render_form(request, form, True)
        return False, getctx("ko", content=content)

    def delete(self, selection):
        User.objects.filter(id__in=selection).delete()
        # for s in selection:
        #     user.delete()
        #     try:
        #         mbox = Mailbox.objects.get(pk=int(s))
        #     grp = Group.objects.get(name="DomainAdmins")
        #     mbox.user.groups.remove(grp)
        #     mbox.user.save()

    def get(self, request):
        #domadmins = Mailbox.objects.filter(user__groups__name="DomainAdmins")
        domainadmins = User.objects.filter(groups__name="DomainAdmins")
        # domadmins_list = []
        # for admin in domadmins:
        #     domadmins_list += [admin.tohash()]
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

# coding: utf8

from django.utils.translation import ugettext as _
from django.contrib.auth.models import User, Group
from modoboa.lib import _render, getctx, _render_to_string
from forms import *

class Permissions(object):
    @staticmethod
    def is_authorized(user):
        return True

    def get_add_form(self, request):
        raise NotImplementedError

    def add(self, request):
        raise NotImplementedError

    def delete(self, request, selection):
        raise NotImplementedError

    def get(self, request):
        raise NotImplementedError

class SuperAdminsPerms(Permissions):
    title = _("Add super administrator")
    role = "super_admins"

    @staticmethod
    def is_authorized(user):
        return user.is_superuser
    
    def get_add_form(self, request):
        form = SuperAdminForm(request.user)
        return _render(request, 'admin/add_permission.html', {
                "form" : form, 
                "title" : self.title,
                "role": self.role
                })

    def add(self, request):
        form = SuperAdminForm(request.user, request.POST)
        if form.is_valid():
            user = User.objects.get(pk=request.POST["user"])
            user.is_superuser = True
            user.groups.clear()
            user.save()
            return True, None

        content = _render_to_string(request, "admin/add_permission.html", {
                "form" : form,
                "title" : self.title,
                "role" : self.role
                })
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
                             "enabled" : admin.is_active}]
        return SuperAdminsTable(admins_list).render(request)
   

class DomainAdminsPerms(Permissions):
    title = _("Add domain administrator")
    role = "domain_admins"

    @staticmethod
    def is_authorized(user):
        return user.has_perm("admin.view_domains")

    def get_add_form(self, request):
        form = DomainAdminForm()
        return _render(request, 'admin/add_domain_admin.html', {
                "form" : form, 
                "title" : self.title,
                "role" : self.role
                })
    
    def add(self, request):
        form = DomainAdminForm(request.POST)
        if request.POST.has_key("user") and request.POST["user"] != "":
            mboxid = request.POST['user']
            mb = Mailbox.objects.get(pk=mboxid)
            form.fields["user"].choices = [(mboxid, mb),]
        if form.is_valid():
            mb.user.is_superuser = False
            mb.user.groups.add(Group.objects.get(name="DomainAdmins"))
            mb.user.save()
            return True, None
        content = _render_to_string(request, "admin/add_domain_admin.html", {
                "form" : form,
                "title" : self.title,
                "role" : self.role
                })
        return False, getctx("ko", content=content)

    def delete(self, selection):
        for s in selection:
            mbox = Mailbox.objects.get(pk=int(s))
            grp = Group.objects.get(name="DomainAdmins")
            mbox.user.groups.remove(grp)
            mbox.user.save()

    def get(self, request):
        domadmins = Mailbox.objects.filter(user__groups__name="DomainAdmins")
        domadmins_list = []
        for admin in domadmins:
            domadmins_list += [admin.tohash()]
        return DomainAdminsTable(domadmins_list).render(request)

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
    res = events.raiseQueryEvent("PermsGetClass", role=role)
    if not len(res):
        return None
    return res[0]

# coding: utf8

from django.utils.translation import ugettext as _
from django.contrib.auth.models import User, Group
from modoboa.lib import _render
from forms import *

class Permissions(object):
    @staticmethod
    def is_auhorized(user):
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
    @staticmethod
    def is_auhorized(user):
        return user.is_superuser
    
    def get_add_form(self, request):
        form = SuperAdminForm()
        return _render(request, 'admin/add_permission.html', {
                "form" : form, 
                "title" : _("Add super administrator"),
                "role": "super_admins"
                })

    def add(self, request):
        form = SuperAdminForm(request.POST)
        if form.is_valid():
            user = User.objects.get(pk=request.POST["user"])
            user.is_superuser = True
            user.groups.clear()
            user.save()
            return True, None

        ctx = _ctx_ko("admin/add_superadmin.html", {
                "form" : form
                })
        return False, ctx
    
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
    @staticmethod
    def is_auhorized(user):
        return True

    def get_add_form(self, request):
        form = DomainAdminForm()
        return _render(request, 'admin/add_domain_admin.html', {
                "form" : form, "title" : _("Add domain administrator"),
                "role" : "domain_admins"
                })
    
    def add(self, request):
        form = DomainAdminForm(request.POST)
        mboxid = request.POST['user']
        form.fields["user"].choices = \
            [(mboxid, Mailbox.objects.get(pk=mboxid)),]
        if form.is_valid():
            mb = Mailbox.objects.get(pk=request.POST["user"])
            mb.user.is_superuser = False
            mb.user.groups.add(Group.objects.get(name="DomainAdmins"))
            mb.user.save()
            return True, None
        ctx = _ctx_ko("admin/add_domain_admin.html", {
                "form" : form
                })
        return False, ctx

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
    parts = role.split("_")
    cname = ""
    for p in parts:
        cname += p.capitalize()
    cname += "Perms"
    if globals().has_key(cname):
        if globals()[cname].is_auhorized(user):
            return globals()[cname]
        return None
    # else raise event for plugins

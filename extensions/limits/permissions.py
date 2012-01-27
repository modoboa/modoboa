# coding: utf-8

from django.utils.translation import ugettext as _, ugettext_noop
from django.contrib.auth.models import User
from modoboa.admin.permissions import Permissions
from modoboa.admin.lib import grant_access_to_object
from modoboa.admin.models import ObjectAccess
from modoboa.lib import events
from modoboa.lib.webutils import _render, _render_to_string
from tables import *
from forms import *

class ResellersPerms(Permissions):
    title = ugettext_noop("New reseller")
    role = "resellers"
    add_success_msg = ugettext_noop("Reseller added")

    def get_add_form(self, request):
        form = ResellerWithPasswordForm()
        return self._render_form(request, form)

    def add(self, request):
        form = ResellerWithPasswordForm(request.POST)
        error = None
        if form.is_valid():
            r = form.save(group="Resellers")
            grant_access_to_object(request.user, r, True)
            return True, None
        content = self._render_form(request, form, True)
        return False, dict(status="ko", content=content)

    def delete(self, selection):
        ct = ContentType.objects.get_for_model(User)
        for u in User.objects.filter(id__in=selection):
            try:
                ObjectOwner.objects.get(content_type=ct, object_id=u.id).delete()
            except ObjectOwner.DoesNotExist:
                pass
            u.delete()
        

    def get(self, request):
        resellers = User.objects.filter(groups__name="Resellers")
        return ResellersTable(request, resellers).render()

@events.observe('PermsGetTables')
def get_resellers_table(request):
    if not request.user.is_superuser:
        return []
    return [{"id" : "resellers",
             "title" : _("Resellers"),
             "rel" : "350 300",
             "content" : ResellersPerms().get(request)}]

@events.observe("PermsGetClass")
def get_perms_class(role):
    if role != "resellers":
        return []
    return [ResellersPerms]

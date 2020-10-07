"""Alias related views."""

from reversion import revisions as reversion

from django.contrib.auth import mixins as auth_mixins
from django.contrib.auth.decorators import login_required, permission_required
from django.db import IntegrityError
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext as _, ungettext
from django.views import generic

from modoboa.core import signals as core_signals
from modoboa.lib.exceptions import Conflict, PermDeniedException
from modoboa.lib.web_utils import render_to_json_response
from ..forms import AliasForm
from ..models import Alias


def _validate_alias(request, form, successmsg, callback=None):
    """Alias validation

    Common function shared between creation and modification actions.
    """
    if form.is_valid():
        try:
            alias = form.save()
        except IntegrityError:
            raise Conflict(_("Alias with this name already exists"))
        if callback:
            callback(request.user, alias)
        return render_to_json_response(successmsg)

    return render_to_json_response({"form_errors": form.errors}, status=400)


def _new_alias(request, title, action, successmsg,
               tplname="admin/aliasform.html"):
    core_signals.can_create_object.send(
        "new_alias", context=request.user, klass=Alias)
    if request.method == "POST":
        def callback(user, alias):
            alias.post_create(user)

        form = AliasForm(request.user, request.POST)
        return _validate_alias(
            request, form, successmsg, callback
        )

    ctx = {
        "title": title,
        "action": action,
        "formid": "aliasform",
        "action_label": _("Create"),
        "action_classes": "submit",
        "form": AliasForm(request.user)
    }
    return render(request, tplname, ctx)


@login_required
@permission_required("admin.add_alias")
@reversion.create_revision()
def newalias(request):
    return _new_alias(
        request, _("New alias"), reverse("admin:alias_add"),
        _("Alias created")
    )


@login_required
@permission_required("admin.change_alias")
@reversion.create_revision()
def editalias(request, alid, tplname="admin/aliasform.html"):
    alias = Alias.objects.get(pk=alid)
    if not request.user.can_access(alias):
        raise PermDeniedException
    if request.method == "POST":
        successmsg = _("Alias modified")
        form = AliasForm(request.user, request.POST, instance=alias)
        return _validate_alias(request, form, successmsg)

    ctx = {
        "action": reverse("admin:alias_change", args=[alias.id]),
        "formid": "aliasform",
        "title": alias.address,
        "action_label": _("Update"),
        "action_classes": "submit",
        "form": AliasForm(request.user, instance=alias)
    }
    return render(request, tplname, ctx)


@login_required
@permission_required("admin.delete_alias")
def delalias(request):
    selection = request.GET["selection"].split(",")
    for alid in selection:
        alias = Alias.objects.get(pk=alid)
        if not request.user.can_access(alias):
            raise PermDeniedException
        alias.delete()
    msg = ungettext("Alias deleted", "Aliases deleted", len(selection))
    return render_to_json_response(msg)


class AliasDetailView(
        auth_mixins.PermissionRequiredMixin, generic.DetailView):
    """DetailView for Alias."""

    model = Alias
    permission_required = "admin.add_alias"

    def has_permission(self):
        """Check object-level access."""
        result = super(AliasDetailView, self).has_permission()
        if not result:
            return result
        return self.request.user.can_access(self.get_object())

    def get_context_data(self, **kwargs):
        """Add information to context."""
        context = super(AliasDetailView, self).get_context_data(**kwargs)
        context["selection"] = "identities"
        return context

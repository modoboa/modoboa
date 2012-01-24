# coding: utf-8
from django.utils.translation import ugettext as _
from django.db import IntegrityError, transaction
from django.contrib.auth.models import *
from django.contrib import messages
from django.contrib.auth.decorators \
    import login_required, user_passes_test, permission_required
from django.core.urlresolvers import reverse
from forms import *
from modoboa.lib.webutils import _render, ajax_response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_reseller(request, resid, tplname="admin/add_permission.html"):
    reseller = User.objects.get(pk=resid)
    ctx = dict(title=_("Edit reseller"), submit_label=_("Update"),
               addurl=reverse(edit_reseller, args=[resid]))
    if request.method == "POST":
        if request.POST.get("password1", "") != "" and \
                request.POST.get("password2", "") != "":
            form = ResellerWithPasswordForm(request.POST, instance=reseller)
        else:
            form = ResellerForm(request.POST, instance=reseller)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                error = _("User with this Username already exists")
            else:
                messages.info(request, _("Reseller updated"), fail_silently=True)
                return ajax_response(request, 
                                     url=reverse("modoboa.admin.views.permissions"))

        ctx.update(form=form, error=error)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    form = ResellerWithPasswordForm(instance=reseller)
    ctx.update(form=form)
    return _render(request, tplname, ctx)

@login_required
@permission_required("auth.view_permissions")
@transaction.commit_on_success
def edit_limits_pool(request, resid, tplname="limits/pool.html"):
    reseller = User.objects.get(pk=resid)
    ctx = dict(reseller=reseller)
    if request.method == "POST":
        form = ResellerPoolForm(request.POST)
        if form.is_valid():
            form.save_new_limits(reseller.limitspool)
            messages.info(request, _("Pool updated"), fail_silently=True)
            return ajax_response(request, url=reverse("modoboa.admin.views.permissions"))
        ctx.update(form=form)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    form = ResellerPoolForm()
    form.load_from_user(reseller)
    ctx.update(form=form)
    return _render(request, tplname, ctx)

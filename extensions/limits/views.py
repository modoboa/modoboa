# coding: utf-8
from django.utils.translation import ugettext as _, ungettext
from django.db import IntegrityError
from django.contrib.auth.models import *
from django.contrib import messages
from django.contrib.auth.decorators \
    import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from tables import *
from forms import *
from modoboa.lib import parameters
from modoboa.lib.webutils import _render, ajax_response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def resellers(request, tplname="limits/resellers.html"):
    users = User.objects.filter(groups__name="Resellers")
    paginator = Paginator(users, 
                          int(parameters.get_admin("ITEMS_PER_PAGE", app="admin")))
    page = int(request.GET.get("page", "1"))
    try:
        subset = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        subset = paginator.page(paginator.num_pages)

    ctx = dict(table=ResellersTable(request, subset.object_list),
               page=subset,
               paginator=paginator)
    return _render(request, tplname, ctx)

def validate_reseller(request, form, action, tplname="limits/reseller.html"):
    error = None
    if form.is_valid():
        try:
            form.save()
        except IntegrityError:
            error = _("User with this Username already exists")
        else:
            msg = _("Reseller created") if action == "create" \
                else _("Reseller updated")
            messages.info(request, msg, fail_silently=True)
            return ajax_response(request, url=reverse(resellers))
    submit_label = _("Create") if action == "create" else _("Update")
    ctx = dict(form=form, error=error, submit_label=submit_label)
    return ajax_response(request, status="ko", template=tplname, **ctx)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def new_reseller(request, tplname="limits/reseller.html"):
    if request.method == "POST":
        form = ResellerWithPasswordForm(request.POST)
        return validate_reseller(request, form, "create")
        
    form = ResellerWithPasswordForm()
    ctx = dict(form=form, submit_label=_("Create"))
    return _render(request, tplname, ctx)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_reseller(request, resid, tplname="limits/reseller.html"):
    reseller = User.objects.get(pk=resid)
    if request.method == "POST":
        if request.POST.get("password1", "") != "" and \
                request.POST.get("password2", "") != "":
            form = ResellerWithPasswordForm(request.POST, instance=reseller)
        else:
            form = ResellerForm(request.POST, instance=reseller)
        return validate_reseller(request, form, action="update")

    form = ResellerWithPasswordForm(instance=reseller)
    ctx = dict(form=form, submit_label=_("Update"))
    return _render(request, tplname, ctx)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_resellers(request):
    selection = map(lambda idx: int(idx), request.GET.get("selection", "").split(","))
    if not len(selection):
        raise Exception("")

    User.objects.filter(id__in=selection).delete()
    msg = ungettext("Reselled deleted", "Resellers deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_limits_pool(request, resid, tplname="limits/pool.html"):
    reseller = User.objects.get(pk=resid)
    if request.method == "POST":
        form = ResellerPoolForm(request.POST)
        if form.is_valid():
            form.save_new_limits(reseller.limitspool)
            messages.info(request, _("Pool updated"), fail_silently=True)
            return ajax_response(request, url=reverse(resellers))
        ctx = dict(form=form)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    form = ResellerPoolForm()
    form.load_from_user(reseller)
    ctx = dict(form=form, reseller=reseller)
    return _render(request, tplname, ctx)

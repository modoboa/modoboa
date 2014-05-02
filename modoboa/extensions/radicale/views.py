"""
Radicale extension views.
"""
from itertools import chain

from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import (
    login_required
)
from django.utils.translation import ugettext as _

from modoboa.lib.webutils import (
    _render_to_string, render_to_json_response
)
from modoboa.lib.exceptions import NotFound, PermDeniedException
from modoboa.extensions.radicale.forms import (
    UserCalendarWizard, SharedCalendarForm, UserCalendarEditionForm
)
from modoboa.extensions.radicale.models import UserCalendar, SharedCalendar


@login_required
def index(request):
    return render(request, "radicale/calendars.html", {
        "selection": "radicale"
    })


@login_required
def calendars(request, tplname="radicale/calendar_list.html"):
    if request.user.group == "SimpleUsers":
        cals = UserCalendar.objects.filter(
            mailbox=request.user.mailbox_set.all()[0]
        )
    else:
        cals = chain(
            UserCalendar.objects.get_for_admin(request.user),
            SharedCalendar.objects.get_for_admin(request.user)
        )
    return render_to_json_response({
        "table": _render_to_string(request, tplname, {
            "calendars": cals
        })
    })


@login_required
def new_user_calendar(request):
    return UserCalendarWizard(request).process()


@login_required
def user_calendar(request, pk):
    """
    """
    try:
        ucal = UserCalendar.objects.get(pk=pk)
    except UserCalendar.DoesNotExist:
        raise NotFound
    instances = {"general": ucal, "rights": ucal}
    if request.method == "DELETE":
        # Check ownership
        ucal.delete()
        return render_to_json_response(_("Calendar removed"))
    return UserCalendarEditionForm(request, instances=instances).process()


@login_required
def new_shared_calendar(request):
    if request.method == "POST":
        form = SharedCalendarForm(request.POST)
        if form.is_valid():
            form.save()
            return render_to_json_response(_("Calendar created"))
        return render_to_json_response(
            {"form_errors": form.errors}, status=400
        )
    form = SharedCalendarForm()
    return render(request, "common/generic_modal_form.html", {
        "form": form,
        "formid": "newsharedcal_form",
        "title": _("New shared calendar"),
        "action": reverse("new_shared_calendar"),
        "action_classes": "submit",
        "action_label": _("Submit")
    })


@login_required
def shared_calendar(request, pk):
    """
    """
    try:
        scal = SharedCalendar.objects.get(pk=pk)
    except SharedCalendar.DoesNotExist:
        raise NotFound
    if not request.user.can_access(scal.domain):
        raise PermDeniedException
    if request.method == "DELETE":
        scal.delete()
        return render_to_json_response(_("Calendar removed"))
  

"""
Radicale extension views.
"""
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import (
    login_required
)
from django.utils.translation import ugettext as _
from modoboa.extensions.radicale.forms import UserCalendarWizard


@login_required
def index(request):
    return HttpResponseRedirect(reverse(calendars))


@login_required
def calendars(request, tplname="radicale/calendars.html"):
    return render(request, tplname, {
        "selection": "radicale"
    })


@login_required
def new_calendar(request, tplname="common/wizard_forms.html"):
    wizard = UserCalendarWizard(request)
    if request.method == "POST":
        return wizard.validate_step()
    wizard.create_forms()
    return render(request, tplname, {
        "title": _("New calendar"),
        "action": reverse(new_calendar),
        "formid": "newcal_form",
        "wizard": wizard
    })

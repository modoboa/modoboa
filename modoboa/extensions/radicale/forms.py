"""
Radicale extension forms.
"""
from django import forms
from django.utils.translation import ugettext as _
from modoboa.lib.webutils import render_to_json_response
from modoboa.lib.formutils import WizardForm
from modoboa.extensions.radicale.models import UserCalendar


class UserCalendarForm(forms.ModelForm):
    """
    User calendar form.
    """
    class Meta:
        model = UserCalendar
        fields = ('name', )


class RightsForm(forms.Form):
    username = forms.CharField(required=False)


class UserCalendarWizard(WizardForm):
    """
    """
    def __init__(self, request):
        super(UserCalendarWizard, self).__init__(request)
        self.add_step(UserCalendarForm, _("General"))
        self.add_step(RightsForm, _("Rights"))

    def done(self, request):
        calendar = self.first_step.form.save(commit=False)
        calendar.mailbox = request.user.mailbox_set.all()[0]
        calendar.save()
        return render_to_json_response(_("Calendar created"))

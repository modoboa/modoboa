"""
Radicale extension forms.
"""
from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib.webutils import render_to_json_response
from modoboa.lib.formutils import WizardForm, TabForms, DynamicForm
from modoboa.extensions.radicale.models import UserCalendar, SharedCalendar


class UserCalendarForm(forms.ModelForm):
    """
    User calendar form.
    """
    class Meta:
        model = UserCalendar
        fields = ('name', )


class SharedCalendarForm(forms.ModelForm):
    """
    Shared calendar form.
    """
    class Meta:
        model = SharedCalendar


class RightsForm(forms.Form, DynamicForm):
    """
    """
    username = forms.CharField(required=False)
    read_access = forms.BooleanField(initial=False, label=_("Read"))
    write_access = forms.BooleanField(initial=False, label=_("Write"))

    def __init__(self, *args, **kwargs):
        from django.http import QueryDict

        if "instance" in kwargs:
            self.calendar = kwargs["instance"]
            del kwargs["instance"]
        else:
            self.calendar = None
        super(RightsForm, self).__init__(*args, **kwargs)

        if args and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "username", forms.EmailField)

    def _create_field(self, typ, name, value=None, pos=None):
        """
        """
        super(RightsForm, self)._create_field(typ, name, value, pos)


class UserCalendarWizard(WizardForm):
    """Custom wizard to create a new calendar.

    """
    def __init__(self, request):
        super(UserCalendarWizard, self).__init__(request)
        self.add_step(UserCalendarForm, _("General"))
        self.add_step(RightsForm, _("Rights"))

    def extra_context(self, context):
        context.update({
            "title": _("New calendar"),
            "action": reverse("new_user_calendar"),
            "formid": "newcal_form"
        })

    def done(self):
        calendar = self.first_step.form.save(commit=False)
        calendar.mailbox = self.request.user.mailbox_set.all()[0]
        calendar.save()
        return render_to_json_response(_("Calendar created"))


class UserCalendarEditionForm(TabForms):
    """User calendar edition form.
    """
    def __init__(self, *args, **kwargs):
        self.forms = []
        self.forms.append({
            "id": "general",
            "title": _("General"),
            "cls": UserCalendarForm,
            "mandatory": True
        })
        self.forms.append({
            "id": "rights",
            "title": _("Rights"),
            "cls": RightsForm,
            "formtpl": "radicale/rightsform.html",
            "mandatory": True
        })
        super(UserCalendarEditionForm, self).__init__(*args, **kwargs)

    def extra_context(self, context):
        context.update({
            "title": self.instances["general"].name,
            "formid": "ucal_form"
        })

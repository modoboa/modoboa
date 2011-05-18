from django import forms
from django.utils.translation import ugettext as _
from modoboa.admin.templatetags.admin_extras import gender

class FiltersSetForm(forms.Form):
    name = forms.CharField()
    active = forms.BooleanField(label=gender("Active", "m"), required=False, 
                                initial=False,
                                help_text=_("Check to activate this filters set"))


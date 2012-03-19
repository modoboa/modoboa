from django import forms
from models import ARmessage
from django.utils.translation import ugettext as _
import datetime

class ARmessageForm(forms.ModelForm):
    untildate = forms.DateField(
        label=_('Until'), required=False,
        help_text=_("Activate your auto reply until this date")
        )

    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled')

    def clean_untildate(self):
        if self.cleaned_data["untildate"] is not None:
            if self.cleaned_data["untildate"] < datetime.date.today():
                raise forms.ValidationError(_("This date is over"))
        return self.cleaned_data['untildate']

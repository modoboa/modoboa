# coding: utf-8
import datetime
from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy
from .models import ARmessage


class ARmessageForm(forms.ModelForm):
    untildate = forms.DateField(
        label=ugettext_lazy('Until'),
        required=False,
        help_text=ugettext_lazy("Activate your auto reply until this date")
    )

    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled')

    def __init__(self, *args, **kwargs):
        super(ARmessageForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['subject', 'content', 'untildate', 'enabled']

    def clean_untildate(self):
        if self.cleaned_data["untildate"] is not None:
            if self.cleaned_data["untildate"] < datetime.date.today():
                raise forms.ValidationError(_("This date is over"))
        return self.cleaned_data['untildate']

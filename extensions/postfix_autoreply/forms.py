from django import forms
from models import ARmessage
from django.utils.translation import ugettext as _
import datetime

class ARmessageForm(forms.ModelForm):
    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled', 'untildate')

    def __init__(self, *args, **kwargs):
        super(ARmessageForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['size'] = 40
        self.fields['content'].widget.attrs['cols'] = 50

    def clean_untildate(self):
        if self.cleaned_data["untildate"] < datetime.date.today():
            raise forms.ValidationError(_("This date is over"))
        return self.cleaned_data['untildate']

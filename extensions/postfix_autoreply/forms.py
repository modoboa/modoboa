from django import forms
from models import ARmessage
from django.utils.translation import ugettext as _

class ARmessageForm(forms.ModelForm):
    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled', 'untildate')

    def __init__(self, *args, **kwargs):
        super(ARmessageForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['size'] = 40
        self.fields['content'].widget.attrs['cols'] = 50

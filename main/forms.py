from django import forms
from mailng.main.models import ARmessage

class ARmessageForm(forms.ModelForm):
    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled')


from django import forms
from django.utils.translation import ugettext as _

class ComposeMailForm(forms.Form):
    from_ = forms.CharField(label=_("From"))
    to = forms.CharField(label=_("To"), widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}))
    cc = forms.CharField(label=_("Cc"), widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}), required=False)
    subject = forms.CharField(label=_("Subject"), max_length=255)


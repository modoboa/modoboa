from django import forms
from django.utils.translation import ugettext as _

class ComposeMailForm(forms.Form):
    from_ = forms.CharField(label=_("From"))
    to = forms.CharField(label=_("To"), widget=forms.Textarea())
    cc = forms.CharField(label=_("Cc"), widget=forms.Textarea(), required=False)
    subject = forms.CharField(label=_("Subject"), max_length=255)

class FolderForm(forms.Form):
    name = forms.CharField()

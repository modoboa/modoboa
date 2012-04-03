from django import forms
from django.utils.translation import ugettext_noop as _

class ComposeMailForm(forms.Form):
    from_ = forms.CharField(label=_("From"))
    to = forms.CharField(label=_("To"))
    cc = forms.CharField(label=_("Cc"), required=False)
    subject = forms.CharField(label=_("Subject"), max_length=255, required=False)

    origmsgid = forms.CharField(label="", widget=forms.HiddenInput(), required=False)
    
class FolderForm(forms.Form):
    oldname = forms.CharField(label="", widget=forms.HiddenInput(), required=False)
    name = forms.CharField()

class AttachmentForm(forms.Form):
    attachment = forms.FileField(label=_("Select a file"))

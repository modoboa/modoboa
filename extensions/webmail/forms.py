from django import forms
from django.utils.translation import ugettext_noop as _

class ComposeMailForm(forms.Form):
    from_ = forms.CharField(label=_("From"))
    to = forms.CharField(label=_("To"), widget=forms.Textarea())
    cc = forms.CharField(label=_("Cc"), widget=forms.Textarea(), required=False)
    subject = forms.CharField(label=_("Subject"), max_length=255, required=False)

class FolderForm(forms.Form):
    name = forms.CharField()

class AttachmentForm(forms.Form):
    attachment = forms.FileField(label=_("Select a file"))

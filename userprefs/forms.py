from django import forms
from models import ARmessage
from mailng.lib.authbackends import check_password
from django.utils.translation import ugettext as _

class ARmessageForm(forms.ModelForm):
    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled', 'untildate')

    def __init__(self, *args, **kwargs):
        super(ARmessageForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['size'] = 40
        self.fields['content'].widget.attrs['cols'] = 50

class ChangePasswordForm(forms.Form):
    oldpassword = forms.CharField(label=_("Old password"), 
                                  widget=forms.PasswordInput)
    newpassword = forms.CharField(label=_("New password"), 
                                  widget=forms.PasswordInput)
    confirmation = forms.CharField(label=_("Confirmation"), 
                                   widget=forms.PasswordInput)

    def __init__(self, mb, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.mbox = mb

    def clean_oldpassword(self):
        if not check_password(self.cleaned_data["oldpassword"], 
                              self.mbox.password):
            raise forms.ValidationError(_("Old password mismatchs"))
        return self.cleaned_data["oldpassword"]

    def clean_confirmation(self):
        if self.cleaned_data["newpassword"] != self.cleaned_data["confirmation"]:
            raise forms.ValidationError(_("Passwords mismatch"))
        return self.cleaned_data["confirmation"]

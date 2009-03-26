from django import forms
from mailng.admin.models import Domain, Mailbox, Alias

class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain

class MailboxForm(forms.ModelForm):
    quota = forms.IntegerField(label="Quota", required=False)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmation", widget=forms.PasswordInput)
    enabled = forms.BooleanField(label="Enabled", required=False)

    class Meta:
        model = Mailbox
        fields = ('name', 'address')

    def clean_password2(self):
        if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
            raise forms.ValidationError("Passwords mismatch")
        return self.cleaned_data["password2"]

class AliasForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        domain = None
        if kwargs.has_key("domain"):
            domain = kwargs["domain"]
            del kwargs["domain"]
        super(AliasForm, self).__init__(*args, **kwargs)
        if domain:
            self.fields['mbox'].queryset = Mailbox.objects.filter(domain=domain.id)

    class Meta:
        model = Alias
        fields = ('address', 'mbox', 'enabled')


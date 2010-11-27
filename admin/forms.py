from django import forms
from modoboa.admin.models import Domain, Mailbox, Alias
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from modoboa.admin.templatetags.admin_extras import gender
from modoboa.lib import tables

class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain
        
    def __init__(self, *args, **kwargs):
        super(DomainForm, self).__init__(*args, **kwargs)
        for f in ['name', 'quota']:
            self.fields[f].widget.attrs['size'] = 14

class MailboxForm(forms.ModelForm):
    quota = forms.IntegerField(label=_("Quota"), required=False,
                               help_text=_("Mailbox quota in MB (default to domain quota if blank)"))
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput,
                                help_text=_("Password used to log in"))
    password2 = forms.CharField(label=_("Confirmation"), widget=forms.PasswordInput,
                                help_text=_("Password confirmation"))
    enabled = forms.BooleanField(label=gender("Enabled", "f"), required=False, 
                                 initial=True,
                                 help_text=_("Check to activate this mailbox"))

    class Meta:
        model = Mailbox
        fields = ('name', 'address')

    def __init__(self, *args, **kwargs):
        super(MailboxForm, self).__init__(*args, **kwargs)
        for f in ['name', 'address', 'quota', 'password1', 'password2']:
            self.fields[f].widget.attrs['size'] = 14

    def clean_password2(self):
        if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
            raise forms.ValidationError(_("Passwords mismatch"))
        return self.cleaned_data["password2"]

class AliasForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        domain = None
        if kwargs.has_key("domain"):
            domain = kwargs["domain"]
            del kwargs["domain"]
        super(AliasForm, self).__init__(*args, **kwargs)
        self.fields['address'].widget.attrs['size'] = 14
        self.fields['mboxes'].widget.attrs['size'] = 5
        if domain:
            self.fields['mboxes'].queryset = Mailbox.objects.filter(domain=domain.id)

    class Meta:
        model = Alias
        fields = ('address', 'mboxes', 'enabled')

class SuperAdminForm(forms.Form):
    user = forms.ModelChoiceField([], label=_("User"), required=True,
                                  empty_label=_("Select a user"),
                                  help_text=_("Select a user in the list"))

    def __init__(self, user, *args, **kwargs):
        super(SuperAdminForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.exclude(pk__in=[1, user.id])

class DomainAdminForm(forms.Form):
    domain = forms.ModelChoiceField(queryset=Domain.objects.all(), label=_("Domain"), 
                                    required=True,
                                    empty_label=_("Select a domain"),
                                    help_text=_("Select a domain in the list"))
    user = forms.ChoiceField(label=_("User"), required=True,
                             choices=[("", _("Empty"))],
                             help_text=_("Select a user in the list"))

class SuperAdminsTable(tables.Table):
    idkey = "id"
    selection = tables.SelectionColumn("selection", width="4%", first=True)
    _1_user_name = tables.Column("user_name", label=_("User name"))
    _2_full_name = tables.Column("full_name", label=_("Full name"))
    _3_enabled = tables.Column("enabled", label=_("Enabled_m"), width="10%")
    
class DomainAdminsTable(tables.Table):
    idkey = "id"
    selection = tables.SelectionColumn("selection", width="4%", first=True)
    _1_domain = tables.Column("domain", label=_("Domain"))
    _2_full_name = tables.Column("full_name", label=_("Full name"))
    _3_enabled = tables.Column("enabled", label=_("Enabled_m"), width="10%")
    

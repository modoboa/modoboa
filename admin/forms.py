# coding: utf8
from django import forms
from modoboa.admin.models import *
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

class ProxyForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(ProxyForm, self).__init__(*args, **kwargs)

        if user.is_superuser:
            self._domain = None
        else:
            self._domain = user.mailbox_set.all()[0].domain

class DomainAliasForm(ProxyForm):
    class Meta:
        model = DomainAlias
        fields = ('name', 'target', 'enabled')

    def __init__(self, *args, **kwargs):
        super(DomainAliasForm, self).__init__(*args, **kwargs)
        if self._domain is not None:
            self.fields["target"].queryset = Domain.objects.filter(pk=self._domain.id)

class MailboxForm(ProxyForm):
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
        fields = ('domain', 'name', 'address')

    def __init__(self, *args, **kwargs):
        super(MailboxForm, self).__init__(*args, **kwargs)
        for f in ['name', 'address', 'quota', 'password1', 'password2']:
            self.fields[f].widget.attrs['size'] = 14
        if self._domain is not None:
            self.fields["domain"].queryset = Domain.objects.filter(pk=self._domain.id)
            self.fields["domain"].initial = self._domain

        if kwargs.has_key("instance"):
            self.fields['quota'].initial = kwargs["instance"].quota
            self.fields['enabled'].initial = kwargs["instance"].user.is_active
            self.fields['password1'].initial = "é"
            self.fields['password2'].initial = "é"

    def clean_address(self):
        if self.cleaned_data["address"].find('@') != -1:
            return self.cleaned_data["address"].rsplit("@", 1)[0]
        return self.cleaned_data["address"]

    def clean_password2(self):
        if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
            raise forms.ValidationError(_("Passwords mismatch"))
        return self.cleaned_data["password2"]

    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(MailboxForm, self).save(commit=False)
        if commit:
            m.save(enabled=self.cleaned_data["enabled"], 
                   password=self.cleaned_data["password1"],
                   quota=self.cleaned_data["quota"])
        return m

class AliasForm(ProxyForm):
    domain = forms.ModelChoiceField(queryset=Domain.objects.all(), label=_("Domain"),
                                    required=True,
                                    empty_label=_("Select a domain"),
                                    help_text=_("Select a domain in the list"))

    def __init__(self, *args, **kwargs):
        super(AliasForm, self).__init__(*args, **kwargs)
        self.fields['address'].widget.attrs['size'] = 14
        self.fields['mboxes'].widget.attrs['size'] = 5

        # This part is a little bit tricky. As 'domain' is not a
        # member of Alias, we need to fill it manually. if
        # self._domain exists, it means a DomainAdmin is going to
        # create a new alias, we know how to fill the fields. Else,
        # leave them empty (super admin mode).
        if self._domain is not None:
            self.fields["domain"].queryset = Domain.objects.filter(pk=self._domain.id)
        elif len(args) < 2 or args[1]["domain"] == '':
            self.fields['mboxes'].queryset = Mailbox.objects.none()
        
        # if 'instance' exists, it means we are modifying an existing
        # record, we need to select the right value for
        # 'domain'. Finally, if super user is doing the job, we need
        # to fill 'mboxes' because it's currently empty (see upper).
        if kwargs.has_key("instance") or self._domain is not None:
            domain = self._domain is None and kwargs["instance"].domain or self._domain
            self.fields["domain"].initial = domain
            self.fields['mboxes'].queryset = Mailbox.objects.filter(domain=domain)
        
        self.fields.keyOrder = ['domain', 'address', 'mboxes', 'enabled']

    class Meta:
        model = Alias
        fields = ('address', 'mboxes', 'enabled')

    def clean_address(self):
        if self.cleaned_data["address"].find('@') != -1:
            return self.cleaned_data["address"].rsplit("@", 1)[0]
        return self.cleaned_data["address"]

    def save(self, force_insert=False, force_update=False, commit=True):
        a = super(AliasForm, self).save(commit=False)
        if commit:
            domain = self.cleaned_data["domain"].name
            a.save()
        return a

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
    

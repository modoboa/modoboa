# coding: utf-8
from django import forms
from modoboa.admin.models import *
from modoboa.admin.lib import is_domain_admin
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from modoboa.admin.templatetags.admin_extras import gender
from modoboa.lib import tables
from modoboa.lib.emailutils import split_mailbox

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
    password1 = forms.CharField(label=_("Password"), 
                                widget=forms.PasswordInput(render_value=True),
                                help_text=_("Password used to log in"))
    password2 = forms.CharField(label=_("Confirmation"), 
                                widget=forms.PasswordInput(render_value=True),
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

    def commit_save(self, mb):
        mb.save(enabled=self.cleaned_data["enabled"], 
                password=self.cleaned_data["password1"],
                quota=self.cleaned_data["quota"])

    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(MailboxForm, self).save(commit=False)
        if commit:
            self.commit_save(m)
        return m

class AliasForm(ProxyForm):
    targets = forms.CharField(label=_("Target(s)"), required=False,
                              help_text=_("Mailbox(es) this alias will point to"))

    def __init__(self, *args, **kwargs):
        super(AliasForm, self).__init__(*args, **kwargs)
        self.fields['address'].widget.attrs['size'] = 14

        # This part is a little bit tricky. As 'domain' is not a
        # member of Alias, we need to fill it manually. if
        # self._domain exists, it means a DomainAdmin is going to
        # create a new alias, we know how to fill the fields.
        if self._domain is not None:
            self.fields["domain"].queryset = Domain.objects.filter(pk=self._domain.id)
        
        # if 'instance' exists, it means we are modifying an existing
        # record, we need to select the right value for 'domain' and
        # to fill the first "targets" input (because it is created by the
        # Form object, not by us).
        domain = None
        if self._domain:
            domain = self._domain
        if kwargs.has_key("instance"):
            if self._domain is None:
                domain = kwargs["instance"].domain
            self.fields["targets"].initial = kwargs["instance"].first_target()
        if domain is not None:
            self.fields["domain"].initial = domain
        
        self.fields.keyOrder = ['address', 'domain', 'enabled', 'targets']

    class Meta:
        model = Alias
        fields = ('address', 'domain', 'enabled')

    def clean_address(self):
        if self.cleaned_data["address"].find('@') != -1:
            return self.cleaned_data["address"].rsplit("@", 1)[0]
        return self.cleaned_data["address"]

    def set_targets(self, user, values):
        self.ext_targets = []
        self.int_targets = []
        umb = Mailbox.objects.get(user=user.id)
        for addr in values:
            if addr == "":
                continue
            local_part, domain = split_mailbox(addr)
            if domain is None:
                raise AdminError("%s %s" % (_("Invalid mailbox"), addr))
            if is_domain_admin(user) and umb.domain.name != domain:
                try:
                    d = Domain.objects.get(name=domain)
                except Domain.DoesNotExist:
                    pass
                else:
                    raise AdminError("%s %s" % (_("Access denied for"), addr))
            try:
                mb = Mailbox.objects.get(address=local_part, domain__name=domain)
            except Mailbox.DoesNotExist:
                self.ext_targets += [addr]
            else:
                if not user.is_superuser:
                    usermb = Mailbox.objects.get(user=user.id)
                    if usermb.domain.id != mb.domain.id:
                        raise AdminError("%s %s" % (_("Permission denied on"), addr))
                self.int_targets += [mb]

    def save(self, force_insert=False, force_update=False, commit=True):
        a = super(AliasForm, self).save(commit=False)
        if commit:
            a.save(self.int_targets, self.ext_targets)
            self.save_m2m()
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
    _3_date_joined = tables.Column("date_joined", label=_("Defined"))
    _4_enabled = tables.Column("enabled", label=gender("Enabled", "m"), width="10%")
    
class DomainAdminsTable(tables.Table):
    idkey = "id"
    selection = tables.SelectionColumn("selection", width="4%", first=True)
    _1_domain = tables.Column("domain", label=_("Domain"))
    _2_full_name = tables.Column("full_name", label=_("Full name"))
    _3_date_joined = tables.Column("date_joined", label=_("Defined"))
    _4_enabled = tables.Column("enabled", label=gender("Enabled", "m"), width="10%")
    

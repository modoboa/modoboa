# coding: utf-8
from django import forms
from modoboa.admin.models import *
from modoboa.admin.lib import is_domain_admin
from django.utils.translation import ugettext as _, ugettext_noop
from django.contrib.auth.models import User
from modoboa.admin.templatetags.admin_extras import gender
from modoboa.lib import tables
from modoboa.lib.emailutils import split_mailbox
from lib import get_user_domains, get_user_domains_qs

class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain
        fields = ("name", "quota", "enabled")

    def __init__(self, *args, **kwargs):
        self.oldname = None
        if kwargs.has_key("instance"):
            self.oldname = kwargs["instance"].name
        super(DomainForm, self).__init__(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, commit=True):
        d = super(DomainForm, self).save(commit=False)
        if commit:
            if self.oldname is not None and d.name != self.oldname:
                if not d.rename_dir(self.oldname):
                    raise AdminError(_("Failed to rename domain, check permissions"))
            d.save()
        return d

class ProxyForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(ProxyForm, self).__init__(*args, **kwargs)

        if not user.is_superuser:
            self._domains = get_user_domains_qs(user)
        else:
            self._domains = None

class DomainAliasForm(ProxyForm):
    class Meta:
        model = DomainAlias
        fields = ('name', 'target', 'enabled')

    def __init__(self, *args, **kwargs):
        super(DomainAliasForm, self).__init__(*args, **kwargs)
        if self._domains is not None:
            #self.fields["target"].queryset = Domain.objects.filter(pk=self._domain.id)
            self.fields["target"].queryset = self._domains

class MailboxForm(ProxyForm):
    quota = forms.IntegerField(label=ugettext_noop("Quota"), required=False,
                               help_text=ugettext_noop("Mailbox quota in MB (default to domain quota if blank)"))
    password1 = forms.CharField(label=ugettext_noop("Password"), 
                                widget=forms.PasswordInput(render_value=True),
                                help_text=ugettext_noop("Password used to log in"))
    password2 = forms.CharField(label=ugettext_noop("Confirmation"), 
                                widget=forms.PasswordInput(render_value=True),
                                help_text=ugettext_noop("Password confirmation"))
    enabled = forms.BooleanField(label=gender("Enabled", "f"), required=False, 
                                 initial=True,
                                 help_text=ugettext_noop("Check to activate this mailbox"))

    class Meta:
        model = Mailbox
        fields = ('domain', 'name', 'address')

    def __init__(self, *args, **kwargs):
        super(MailboxForm, self).__init__(*args, **kwargs)
        for f in ['name', 'address', 'quota', 'password1', 'password2']:
            self.fields[f].widget.attrs['size'] = 14
        if self._domains is not None:
            self.fields["domain"].queryset = self._domains
            #self.fields["domain"].queryset = Domain.objects.filter(pk=self._domain.id)
            #self.fields["domain"].initial = self._domain

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
    targets = forms.CharField(label=ugettext_noop("Target(s)"), required=False,
                              help_text=ugettext_noop("Mailbox(es) this alias will point to"))

    def __init__(self, *args, **kwargs):
        super(AliasForm, self).__init__(*args, **kwargs)
        self.fields['address'].widget.attrs['size'] = 14

        # This part is a little bit tricky. As 'domain' is not a
        # member of Alias, we need to fill it manually. if
        # self._domain exists, it means a DomainAdmin is going to
        # create a new alias, we know how to fill the fields.
        # if self._domain is not None:
        #     self.fields["domain"].queryset = Domain.objects.filter(pk=self._domain.id)
        
        if self._domains is not None:
            self.fields["domain"].queryset = self._domains

        # if 'instance' exists, it means we are modifying an existing
        # record, we need to select the right value for 'domain' and
        # to fill the first "targets" input (because it is created by the
        # Form object, not by us).
        #domain = None
        # if self._domain:
        #     domain = self._domain
        if kwargs.has_key("instance"):
            # if self._domain is None:
            #     domain = kwargs["instance"].domain
            self.fields["targets"].initial = kwargs["instance"].first_target()

        # if domain is not None:
        #     self.fields["domain"].initial = domain
        
        self.fields.keyOrder = ['address', 'domain', 'enabled', 'targets']

    class Meta:
        model = Alias
        fields = ('address', 'domain', 'enabled')

    def clean_address(self):
        if self.cleaned_data["address"].find('@') != -1:
            return self.cleaned_data["address"].rsplit("@", 1)[0]
        return self.cleaned_data["address"]

    def set_targets(self, user, values):
        """Targets dispatching

        We make a difference between 'local' targets (the ones hosted
        by Modoboa) and 'external targets.
        """
        from modoboa.admin.lib import is_object_owner

        self.ext_targets = []
        self.int_targets = []

        for addr in values:
            if addr == "":
                continue
            local_part, domname = split_mailbox(addr)
            if domname is None:
                raise AdminError("%s %s" % (_("Invalid mailbox"), addr))
            try:
                domain = Domain.objects.get(name=domname)
            except Domain.DoesNotExist:
                domain = None
            if domain:
                if not is_object_owner(user, domain):
                    raise PermDeniedException(addr)
                try:
                    mb = Mailbox.objects.get(domain=domain, address=local_part)
                except Mailbox.DoesNotExist:
                    raise AdminError(_("Mailbox %s does not exist" % addr))
                self.int_targets += [mb]
                continue

            self.ext_targets += [addr]

    def save(self, force_insert=False, force_update=False, commit=True):
        a = super(AliasForm, self).save(commit=False)
        if commit:
            a.save(self.int_targets, self.ext_targets)
            self.save_m2m()
        return a

class SuperAdminForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(SuperAdminForm, self).__init__(*args, **kwargs)

        self.fields["user"] = \
            forms.ModelChoiceField([], label=_("User"), required=True,
                                   empty_label=_("Select a user"),
                                   help_text=_("Select a user in the list"))
        self.fields["user"].queryset = User.objects.exclude(pk__in=[1, user.id])

class DomainAdminForm(forms.Form):
    createfrom = forms.ChoiceField(
        choices=[("new", ugettext_noop("Create a new account")),
                 ("select", ugettext_noop("Promote an existing account"))],
        widget=forms.RadioSelect)

    domain = forms.ModelChoiceField(
        queryset=Domain.objects.all(), 
        label=_("Domain"), 
        required=True,
        empty_label=ugettext_noop("Select a domain"),
        help_text=ugettext_noop("Select a domain in the list")
        )
    
    user = forms.ChoiceField(
        label=ugettext_noop("User"), required=True,
        choices=[("", ugettext_noop("Empty"))],
        help_text=ugettext_noop("Select a user in the list"))

class UserForm(forms.ModelForm):
    createmb = forms.BooleanField(
        label=ugettext_noop("Create mailbox"), required=False,
        help_text=ugettext_noop("Create a mailbox for this user using the given address")
        )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True, group=None):
        user = super(UserForm, self).save(commit=False)
        if self.cleaned_data.has_key("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            if group:
                user.groups.add(Group.objects.get(name=group))
                user.save()
        return user

class UserWithPasswordForm(UserForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=ugettext_noop("Confirmation"), 
        widget=forms.PasswordInput,
        help_text=ugettext_noop("Enter the same password as above, for verification.")
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

class DomainAdminPromotionForm(forms.Form):
    name = forms.CharField(
        label=ugettext_noop("Name"),
        help_text=ugettext_noop("The username/email address/name of the account to promote")
        )

    def clean_name(self):
        try:
            u = User.objects.get(username=self.cleaned_data["name"])
        except User.DoesNotExist:
            raise forms.ValidationError(_("Unknown user"))
        return self.cleaned_data["name"]

class ImportDataForm(forms.Form):
    sourcefile = forms.FileField(label=_("Select a file"))
    sepcar = forms.CharField(label=_("Separator"), max_length=1, required=False)

    def clean_sepcar(self):
        if self.cleaned_data["sepcar"] == "":
            return ";"
        return self.cleaned_data["sepcar"]


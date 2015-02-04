from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy
from django.http import QueryDict
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters
from modoboa.lib.exceptions import PermDeniedException, Conflict, NotFound
from modoboa.lib.permissions import get_account_roles
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.formutils import (
    DomainNameField, DynamicForm, TabForms, WizardForm
)
from modoboa.lib.webutils import render_to_json_response
from modoboa.core.models import User
from modoboa.extensions.admin.models import (
    Domain, Mailbox, Alias
)


class AccountFormGeneral(forms.ModelForm):
    username = forms.CharField(
        label=ugettext_lazy("Username"),
        help_text=ugettext_lazy(
            "The user's name. Must be a valid e-mail address for simple users "
            "or administrators with a mailbox."
        )
    )
    role = forms.ChoiceField(
        label=ugettext_lazy("Role"),
        choices=[('', ugettext_lazy("Choose"))],
        help_text=ugettext_lazy("What level of permission this user will have")
    )
    password1 = forms.CharField(
        label=ugettext_lazy("Password"), widget=forms.widgets.PasswordInput
    )
    password2 = forms.CharField(
        label=ugettext_lazy("Confirmation"),
        widget=forms.widgets.PasswordInput,
        help_text=ugettext_lazy(
            "Enter the same password as above, for verification."
        )
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "role", "is_active")

    def __init__(self, user, *args, **kwargs):
        super(AccountFormGeneral, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['role', 'username', 'first_name', 'last_name',
                                'password1', 'password2', 'is_active']
        self.fields["is_active"].label = _("Enabled")
        self.user = user
        if user.group == "DomainAdmins":
            self.fields["role"] = forms.CharField(
                label="",
                widget=forms.HiddenInput(attrs={"class": "form-control"}),
                required=False
            )
        else:
            self.fields["role"].choices = [('', ugettext_lazy("Choose"))]
            self.fields["role"].choices += \
                get_account_roles(user, kwargs['instance']) \
                if 'instance' in kwargs else get_account_roles(user)

        if "instance" in kwargs:
            account = kwargs["instance"]
            domain_disabled = account.mailbox_set.count() and \
                not account.mailbox_set.all()[0].domain.enabled
            if domain_disabled:
                self.fields["is_active"].widget.attrs['disabled'] = "disabled"
            if args:
                if args[0].get("password1", "") == "" \
                   and args[0].get("password2", "") == "":
                    self.fields["password1"].required = False
                    self.fields["password2"].required = False
                if domain_disabled:
                    del self.fields["is_active"]
            self.fields["role"].initial = account.group
            if not account.is_local \
               and parameters.get_admin("LDAP_AUTH_METHOD", app="core") == "directbind":
                del self.fields["password1"]
                del self.fields["password2"]

    def domain_is_disabled(self):
        """Little shortcut to get the domain's state.

        We need this information inside a template and the form is the
        only object available...

        """
        if not self.instance.mailbox_set.count():
            return False
        return self.instance.mailbox_set.all()[0].domain.enabled == False

    def clean_role(self):
        if self.user.group == "DomainAdmins":
            if self.instance == self.user:
                return "DomainAdmins"
            return "SimpleUsers"
        return self.cleaned_data["role"]

    def clean_username(self):
        from django.core.validators import validate_email
        if not "role" in self.cleaned_data:
            return self.cleaned_data["username"]
        if self.cleaned_data["role"] != "SimpleUsers":
            return self.cleaned_data["username"]
        uname = self.cleaned_data["username"].lower()
        validate_email(uname)
        return uname

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        account = super(AccountFormGeneral, self).save(commit=False)
        if self.user == account and not self.cleaned_data["is_active"]:
            raise PermDeniedException(_("You can't disable your own account"))
        if commit:
            if "password1" in self.cleaned_data \
               and self.cleaned_data["password1"] != "":
                account.set_password(self.cleaned_data["password1"])
            account.save()
            account.set_role(self.cleaned_data["role"])
        return account


class AccountFormMail(forms.Form, DynamicForm):

    """Form to handle mail part."""

    email = forms.EmailField(label=ugettext_lazy("E-mail"), required=False)
    quota = forms.IntegerField(
        label=ugettext_lazy("Quota"),
        required=False,
        help_text=_("Quota in MB for this mailbox. Define a custom value or "
                    "use domain's default one. Leave empty to define an "
                    "unlimited value (not allowed for domain "
                    "administrators)."),
        widget=forms.widgets.TextInput(attrs={"class": "form-control"})
    )
    quota_act = forms.BooleanField(required=False)
    aliases = forms.EmailField(
        label=ugettext_lazy("Alias(es)"),
        required=False,
        help_text=ugettext_lazy(
            "Alias(es) of this mailbox. Indicate only one address per input, "
            "press ENTER to add a new input. Use the '*' character to create "
            "a 'catchall' alias (ex: *@domain.tld)."
        )
    )

    def __init__(self, *args, **kwargs):
        if "instance" in kwargs:
            self.mb = kwargs["instance"]
            del kwargs["instance"]
        else:
            self.mb = None
        super(AccountFormMail, self).__init__(*args, **kwargs)
        self.field_widths = {
            "quota": 3
        }
        self.extra_fields = []
        for fname, field in events.raiseQueryEvent('ExtraFormFields', 'mailform', self.mb):
            self.fields[fname] = field
            self.extra_fields.append(fname)
        if self.mb is not None:
            self.fields["email"].required = True
            cpt = 1
            for alias in self.mb.alias_set.all():
                if len(alias.get_recipients()) >= 2:
                    continue
                name = "aliases_%d" % cpt
                self._create_field(forms.EmailField, name, alias.full_address)
                cpt += 1
            self.fields["email"].initial = self.mb.full_address
            self.fields["quota_act"].initial = self.mb.use_domain_quota
            if not self.mb.use_domain_quota and self.mb.quota:
                self.fields["quota"].initial = self.mb.quota
        else:
            self.fields["quota_act"].initial = True

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "aliases", forms.EmailField)

    def clean_email(self):
        """Ensure lower case emails"""
        return self.cleaned_data["email"].lower()

    def clean(self):
        """Custom fields validation.

        Check if quota is >= 0 only when the domain value is not used.
        """
        super(AccountFormMail, self).clean()
        if self._errors:
            raise forms.ValidationError(self._errors)
        if not self.cleaned_data["quota_act"] \
                and self.cleaned_data['quota'] is not None:
            if self.cleaned_data["quota"] < 0:
                self._errors["quota"] = self.error_class(
                    [_("Must be a positive integer")])
                del self.cleaned_data["quota"]
        return self.cleaned_data

    def create_mailbox(self, user, account):
        """Create a mailbox associated to :kw:`account`."""
        locpart, domname = split_mailbox(self.cleaned_data["email"])
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise NotFound(_("Domain does not exist"))
        if not user.can_access(domain):
            raise PermDeniedException
        try:
            Mailbox.objects.get(address=locpart, domain=domain)
        except Mailbox.DoesNotExist:
            pass
        else:
            raise Conflict(
                _("Mailbox %s already exists" % self.cleaned_data["email"])
            )
        events.raiseEvent("CanCreate", user, "mailboxes")
        self.mb = Mailbox(address=locpart, domain=domain, user=account,
                          use_domain_quota=self.cleaned_data["quota_act"])
        self.mb.set_quota(self.cleaned_data["quota"], 
                          user.has_perm("admin.add_domain"))
        self.mb.save(creator=user)

    def update_mailbox(self, user, account):
        newaddress = None
        if self.cleaned_data["email"] != self.mb.full_address:
            newaddress = self.cleaned_data["email"]
        elif account.group == "SimpleUsers" and account.username != self.mb.full_address:
            newaddress = account.username
        if newaddress is not None:
            self.mb.old_full_address = self.mb.full_address
            local_part, domname = split_mailbox(newaddress)
            try:
                domain = Domain.objects.get(name=domname)
            except Domain.DoesNotExist:
                raise NotFound(_("Domain does not exist"))
            if not user.can_access(domain):
                raise PermDeniedException
            self.mb.rename(local_part, domain)

        self.mb.use_domain_quota = self.cleaned_data["quota_act"]
        override_rules = True \
            if not self.mb.quota or user.has_perm("admin.add_domain") \
            else False
        self.mb.set_quota(self.cleaned_data["quota"], override_rules)
        self.mb.save()
        events.raiseEvent('MailboxModified', self.mb)

    def _update_aliases(self, user, account):
        """Update mailbox aliases."""
        aliases = []
        for name, value in self.cleaned_data.iteritems():
            if not name.startswith("aliases"):
                continue
            if value == "":
                continue
            aliases.append(value.lower())

        for alias in self.mb.alias_set.all():
            if not alias.full_address in aliases:
                if len(alias.get_recipients()) >= 2:
                    continue
                alias.delete()
            else:
                aliases.remove(alias.full_address)
        if not aliases:
            return
        events.raiseEvent(
            "CanCreate", user, "mailbox_aliases", len(aliases)
        )
        for alias in aliases:
            local_part, domname = split_mailbox(alias)
            try:
                self.mb.alias_set.get(address=local_part, domain__name=domname)
            except Alias.DoesNotExist:
                pass
            else:
                continue
            al = Alias(address=local_part, enabled=account.is_active)
            al.domain = Domain.objects.get(name=domname)
            al.save(int_rcpts=[self.mb])
            al.post_create(user)

    def save(self, user, account):
        """Save or update account mailbox."""
        if self.cleaned_data["email"] == "":
            return None

        if self.cleaned_data["quota_act"]:
            self.cleaned_data["quota"] = None

        if not hasattr(self, "mb") or self.mb is None:
            self.create_mailbox(user, account)
        else:
            self.update_mailbox(user, account)
        events.raiseEvent(
            'SaveExtraFormFields', 'mailform', self.mb, self.cleaned_data
        )

        account.email = self.cleaned_data["email"]
        account.save()

        self._update_aliases(user, account)

        return self.mb


class AccountPermissionsForm(forms.Form, DynamicForm):
    domains = DomainNameField(
        label=ugettext_lazy("Domain(s)"),
        required=False,
        help_text=ugettext_lazy("Domain(s) that user administrates")
    )

    def __init__(self, *args, **kwargs):
        if "instance" in kwargs:
            self.account = kwargs["instance"]
            del kwargs["instance"]

        super(AccountPermissionsForm, self).__init__(*args, **kwargs)

        if not hasattr(self, "account") or self.account is None:
            return
        for pos, domain in enumerate(Domain.objects.get_for_admin(self.account)):
            name = "domains_%d" % (pos + 1)
            self._create_field(DomainNameField, name, domain.name)
        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "domains", DomainNameField)

    def save(self):
        current_domains = [
            dom.name for dom in Domain.objects.get_for_admin(self.account)
        ]
        for name, value in self.cleaned_data.items():
            if not name.startswith("domains"):
                continue
            if value in ["", None]:
                continue
            if not value in current_domains:
                domain = Domain.objects.get(name=value)
                domain.add_admin(self.account)

        for domain in Domain.objects.get_for_admin(self.account):
            if not len(filter(lambda name: self.cleaned_data[name] == domain.name,
                              self.cleaned_data.keys())):
                domain.remove_admin(self.account)


class AccountForm(TabForms):
    """Account edition form.

    """
    def __init__(self, request, *args, **kwargs):
        self.user = request.user
        self.forms = [
            dict(id="general", title=_("General"),
                 formtpl="admin/account_general_form.html",
                 cls=AccountFormGeneral,
                 new_args=[self.user], mandatory=True),
            dict(id="mail", title=_("Mail"), formtpl="admin/mailform.html",
                 cls=AccountFormMail),
            dict(id="perms", title=_("Permissions"), formtpl="admin/permsform.html",
                 cls=AccountPermissionsForm)
        ]
        cbargs = [self.user]
        if "instances" in kwargs:
            cbargs += [kwargs["instances"]["general"]]
        self.forms += events.raiseQueryEvent("ExtraAccountForm", *cbargs)

        super(AccountForm, self).__init__(request, *args, **kwargs)

    def extra_context(self, context):
        account = self.instances["general"]
        context.update({
            'title': account.username,
            'formid': 'accountform',
            'action': reverse("admin:account_change", args=[account.id]),
        })

    def check_perms(self, account):
        if account.is_superuser:
            return False
        return self.user.has_perm("admin.add_domain") \
            and account.has_perm("core.add_user")

    def _before_is_valid(self, form):
        if form["id"] == "general":
            return True

        if hasattr(self, "check_%s" % form["id"]):
            if not getattr(self, "check_%s" % form["id"])(self.account):
                return False
            return True

        if False in events.raiseQueryEvent("CheckExtraAccountForm", self.account, form):
            return False
        return True

    def is_valid(self):
        """Two steps validation.
        """
        self.instances["general"].oldgroup = self.instances["general"].group
        if super(AccountForm, self).is_valid(mandatory_only=True):
            self.account = self.forms[0]["instance"].save()
            return super(AccountForm, self).is_valid(optional_only=True)
        return False

    def save(self):
        """Custom save method

        As forms interact with each other, it is simpler to make
        custom code to save them.
        """
        events.raiseEvent(
            "AccountModified", self.instances["general"], self.account
        )
        self.forms[1]["instance"].save(self.user, self.account)
        if len(self.forms) <= 2:
            return
        for f in self.forms[2:]:
            f["instance"].save()

    def done(self):
        return render_to_json_response(_("Account updated"))


class AccountWizard(WizardForm):
    """Account creation wizard.
    """
    def __init__(self, request):
        super(AccountWizard, self).__init__(request)
        self.add_step(
            AccountFormGeneral, _("General"), new_args=[request.user]
        )
        self.add_step(
            AccountFormMail, _("Mail"), formtpl="admin/mailform.html"
        )

    def extra_context(self, context):
        context.update({
            'title': _("New account"),
            'action': reverse("admin:account_add"),
            'formid': 'newaccount_form'
        })

    def done(self):
        from modoboa.lib.webutils import render_to_json_response

        account = self.first_step.form.save()
        account.post_create(self.request.user)
        mailform = self.steps[1].form
        mailform.save(self.request.user, account)
        return render_to_json_response(_("Account created"))

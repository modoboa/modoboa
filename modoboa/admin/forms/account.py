"""Forms related to accounts management."""

from collections import OrderedDict

from django import forms
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.utils.translation import ugettext as _, ugettext_lazy

from passwords.fields import PasswordField

from modoboa.core.models import User
from modoboa.core import signals as core_signals
from modoboa.lib import events, parameters
from modoboa.lib.email_utils import split_mailbox
from modoboa.lib import exceptions as lib_exceptions
from modoboa.lib import fields as lib_fields
from modoboa.lib.form_utils import (
    DynamicForm, TabForms, WizardForm, WizardStep
)
from modoboa.lib.permissions import get_account_roles
from modoboa.lib.validators import validate_utf8_email
from modoboa.lib.web_utils import render_to_json_response

from ..models import Domain, Mailbox, Alias


class AccountFormGeneral(forms.ModelForm):

    """General account form."""

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
    password1 = PasswordField(
        label=ugettext_lazy("Password"), widget=forms.widgets.PasswordInput
    )

    password2 = PasswordField(
        label=ugettext_lazy("Confirmation"),
        widget=forms.widgets.PasswordInput,
        help_text=ugettext_lazy(
            "Enter the same password as above, for verification."
        )
    )

    class Meta:
        model = User
        fields = (
            "username", "first_name", "last_name", "role", "is_active",
            "master_user"
        )

    def __init__(self, user, *args, **kwargs):
        super(AccountFormGeneral, self).__init__(*args, **kwargs)
        self.fields = OrderedDict(
            (key, self.fields[key]) for key in
            ['role', 'username', 'first_name', 'last_name', 'password1',
             'password2', 'master_user', 'is_active']
        )
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

        if not user.is_superuser:
            del self.fields["master_user"]

        if "instance" in kwargs:
            account = kwargs["instance"]
            domain_disabled = (
                hasattr(account, "mailbox") and
                not account.mailbox.domain.enabled
            )
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
               and parameters.get_admin(
                   "LDAP_AUTH_METHOD", app="core") == "directbind":
                del self.fields["password1"]
                del self.fields["password2"]

    def domain_is_disabled(self):
        """Little shortcut to get the domain's state.

        We need this information inside a template and the form is the
        only object available...

        """
        if not hasattr(self.instance, "mailbox"):
            return False
        return not self.instance.mailbox.domain.enabled

    def clean_role(self):
        if self.user.group == "DomainAdmins":
            if self.instance == self.user:
                return "DomainAdmins"
            return "SimpleUsers"
        return self.cleaned_data["role"]

    def clean_username(self):
        """username must be a valid email address for simple users."""
        if "role" not in self.cleaned_data:
            return self.cleaned_data["username"]
        if self.cleaned_data["role"] != "SimpleUsers":
            return self.cleaned_data["username"]
        uname = self.cleaned_data["username"].lower()
        validate_utf8_email(uname)
        return uname

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(
                _("The two password fields didn't match."))
        return password2

    def clean(self):
        """Check master user mode."""
        super(AccountFormGeneral, self).clean()
        if self.errors:
            return self.cleaned_data
        condition = (
            self.cleaned_data.get("master_user") and
            self.cleaned_data["role"] != "SuperAdmins"
        )
        if condition:
            self.add_error(
                "master_user",
                _("Only super administrators are allowed for this mode")
            )
        return self.cleaned_data

    def save(self, commit=True):
        account = super(AccountFormGeneral, self).save(commit=False)
        if self.user == account and not self.cleaned_data["is_active"]:
            raise lib_exceptions.PermDeniedException(
                _("You can't disable your own account"))
        if commit:
            if "password1" in self.cleaned_data \
               and self.cleaned_data["password1"] != "":
                account.set_password(self.cleaned_data["password1"])
            account.save()
            account.role = self.cleaned_data["role"]
        return account


class AccountFormMail(forms.Form, DynamicForm):

    """Form to handle mail part."""

    email = lib_fields.UTF8EmailField(
        label=ugettext_lazy("E-mail"), required=False)
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
    aliases = lib_fields.UTF8AndEmptyUserEmailField(
        label=ugettext_lazy("Alias(es)"),
        required=False,
        help_text=ugettext_lazy(
            "Alias(es) of this mailbox. Indicate only one address per input, "
            "press ENTER to add a new input. Use the '*' character to create "
            "a 'catchall' alias (ex: *@domain.tld)."
        )
    )

    def __init__(self, *args, **kwargs):
        self.mb = kwargs.pop("instance", None)
        super(AccountFormMail, self).__init__(*args, **kwargs)
        self.field_widths = {
            "quota": 3
        }
        self.extra_fields = []
        result = events.raiseQueryEvent('ExtraFormFields', 'mailform', self.mb)
        for fname, field in result:
            self.fields[fname] = field
            self.extra_fields.append(fname)
        if self.mb is not None:
            self.fields["email"].required = True
            cpt = 1
            qset = self.mb.aliasrecipient_set.filter(alias__internal=False)
            for ralias in qset:
                name = "aliases_%d" % cpt
                self._create_field(
                    lib_fields.UTF8AndEmptyUserEmailField, name,
                    ralias.alias.address)
                cpt += 1
            self.fields["email"].initial = self.mb.full_address
            self.fields["quota_act"].initial = self.mb.use_domain_quota
            if not self.mb.use_domain_quota and self.mb.quota:
                self.fields["quota"].initial = self.mb.quota
        else:
            self.fields["quota_act"].initial = True

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(
                args[0], "aliases", lib_fields.UTF8AndEmptyUserEmailField)

    def clean_email(self):
        """Ensure lower case emails"""
        email = self.cleaned_data["email"].lower()
        self.locpart, domname = split_mailbox(email)
        if not domname:
            return email
        try:
            self.domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise forms.ValidationError(_("Domain does not exist"))
        if not self.mb:
            try:
                core_signals.can_create_object.send(
                    sender=self.__class__, context=self.domain,
                    object_type="mailboxes")
            except lib_exceptions.ModoboaException as inst:
                raise forms.ValidationError(inst)
        return email

    def clean(self):
        """Custom fields validation.

        Check if quota is >= 0 only when the domain value is not used.
        """
        super(AccountFormMail, self).clean()
        if not self.cleaned_data["quota_act"] \
                and self.cleaned_data['quota'] is not None:
            if self.cleaned_data["quota"] < 0:
                self.add_error("quota", _("Must be a positive integer"))
        self.aliases = []
        for name, value in self.cleaned_data.iteritems():
            if not name.startswith("aliases"):
                continue
            if value == "":
                continue
            local_part, domname = split_mailbox(value)
            if not Domain.objects.filter(name=domname).exists():
                self.add_error(name, _("Local domain does not exist"))
                break
            self.aliases.append(value.lower())
        return self.cleaned_data

    def create_mailbox(self, user, account):
        """Create a mailbox associated to :kw:`account`."""
        if not user.can_access(self.domain):
            raise lib_exceptions.PermDeniedException
        core_signals.can_create_object.send(
            self.__class__, context=user, object_type="mailboxes")
        self.mb = Mailbox(
            address=self.locpart, domain=self.domain, user=account,
            use_domain_quota=self.cleaned_data["quota_act"])
        self.mb.set_quota(self.cleaned_data["quota"],
                          user.has_perm("admin.add_domain"))
        self.mb.save(creator=user)

    def _update_aliases(self, user, account):
        """Update mailbox aliases."""
        qset = self.mb.aliasrecipient_set.select_related("alias").filter(
            alias__internal=False)
        for ralias in qset:
            if ralias.alias.address not in self.aliases:
                alias = ralias.alias
                ralias.delete()
                if alias.recipients_count > 0:
                    continue
                alias.delete()
            else:
                self.aliases.remove(ralias.alias.address)
        if not self.aliases:
            return
        core_signals.can_create_object.send(
            self.__class__, context=user, object_type="mailbox_aliases",
            count=len(self.aliases))
        core_signals.can_create_object.send(
            self.__class__, context=self.mb.domain,
            object_type="mailbox_aliases", count=len(self.aliases))
        for alias in self.aliases:
            if self.mb.aliasrecipient_set.select_related("alias").filter(
                    alias__address=alias).exists():
                continue
            local_part, domname = split_mailbox(alias)
            al = Alias(address=alias, enabled=account.is_active)
            al.domain = Domain.objects.get(name=domname)
            al.save()
            al.set_recipients([self.mb.full_address])
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
            self.cleaned_data["use_domain_quota"] = (
                self.cleaned_data["quota_act"])
            self.mb.update_from_dict(user, self.cleaned_data)
        events.raiseEvent(
            'SaveExtraFormFields', 'mailform', self.mb, self.cleaned_data
        )

        account.email = self.cleaned_data["email"]
        account.save()

        self._update_aliases(user, account)

        return self.mb


class AccountPermissionsForm(forms.Form, DynamicForm):
    """A form to assign domain(s) permission."""

    domains = lib_fields.DomainNameField(
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
        for pos, dom in enumerate(Domain.objects.get_for_admin(self.account)):
            name = "domains_%d" % (pos + 1)
            self._create_field(lib_fields.DomainNameField, name, dom.name)
        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(
                args[0], "domains", lib_fields.DomainNameField)

    def save(self):
        current_domains = [
            dom.name for dom in Domain.objects.get_for_admin(self.account)
        ]
        for name, value in self.cleaned_data.items():
            if not name.startswith("domains"):
                continue
            if value in ["", None]:
                continue
            if value not in current_domains:
                domain = Domain.objects.get(name=value)
                domain.add_admin(self.account)

        for domain in Domain.objects.get_for_admin(self.account):
            if not filter(lambda name: self.cleaned_data[name] == domain.name,
                          self.cleaned_data.keys()):
                domain.remove_admin(self.account)


class AccountForm(TabForms):

    """Account edition form."""

    def __init__(self, request, *args, **kwargs):
        self.user = request.user
        self.forms = [
            dict(id="general", title=_("General"),
                 formtpl="admin/account_general_form.html",
                 cls=AccountFormGeneral,
                 new_args=[self.user], mandatory=True),
            dict(id="mail",
                 title=_("Mail"), formtpl="admin/mailform.html",
                 cls=AccountFormMail),
            dict(
                id="perms", title=_("Permissions"),
                formtpl="admin/permsform.html",
                cls=AccountPermissionsForm
            )
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
            'action': reverse("admin:account_change",
                              args=[account.id]),
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

        extra_forms = events.raiseQueryEvent(
            "CheckExtraAccountForm", self.account, form)
        if False in extra_forms:
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

    """Account creation wizard."""

    def __init__(self, request):
        super(AccountWizard, self).__init__(request)
        self.add_step(
            WizardStep(
                "general", AccountFormGeneral, _("General"),
                new_args=[request.user]
            )
        )
        self.add_step(
            WizardStep(
                "mail", AccountFormMail, _("Mail"),
                "admin/mailform.html"
            )
        )

    def extra_context(self, context):
        context.update({
            'title': _("New account"),
            'action': reverse("admin:account_add"),
            'formid': 'newaccount_form'
        })

    def done(self):
        from modoboa.lib.web_utils import render_to_json_response

        account = self.first_step.form.save()
        account.post_create(self.request.user)
        mailform = self.steps[1].form
        mailform.save(self.request.user, account)
        return render_to_json_response(_("Account created"))

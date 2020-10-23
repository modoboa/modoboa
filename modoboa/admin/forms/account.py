"""Forms related to accounts management."""

from collections import OrderedDict
from functools import reduce

from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.http import QueryDict
from django.urls import reverse
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.core import signals as core_signals
from modoboa.core.models import User
from modoboa.lib import exceptions as lib_exceptions, fields as lib_fields
from modoboa.lib.email_utils import split_mailbox
from modoboa.lib.form_utils import (
    DynamicForm, TabForms, WizardForm, WizardStep
)
from modoboa.lib.permissions import get_account_roles
from modoboa.lib.validators import validate_utf8_email
from modoboa.lib.web_utils import render_to_json_response, size2integer
from modoboa.parameters import tools as param_tools
from .. import lib, models, signals


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
        choices=[("", ugettext_lazy("Choose"))],
        help_text=ugettext_lazy("What level of permission this user will have")
    )
    random_password = forms.BooleanField(
        label=ugettext_lazy("Random password"),
        help_text=ugettext_lazy(
            "Generate a random password. If you're updating this account and "
            "check this box, a new password will be generated."
        ),
        required=False
    )
    password1 = forms.CharField(
        label=ugettext_lazy("Password"), widget=forms.widgets.PasswordInput,
        required=False
    )

    password2 = forms.CharField(
        label=ugettext_lazy("Confirmation"),
        widget=forms.widgets.PasswordInput,
        help_text=ugettext_lazy(
            "Enter the same password as above, for verification."
        ),
        required=False
    )

    class Meta:
        model = User
        fields = (
            "username", "first_name", "last_name", "role", "is_active",
            "master_user",
        )
        labels = {
            "is_active": ugettext_lazy("Enabled")
        }

    def __init__(self, user, *args, **kwargs):
        super(AccountFormGeneral, self).__init__(*args, **kwargs)
        self.fields = OrderedDict(
            (key, self.fields[key]) for key in
            ["role", "username", "first_name", "last_name",
             "random_password", "password1", "password2",
             "master_user", "is_active"]
        )
        self.user = user
        condition = (
            user.role == "DomainAdmins" or
            user.role == "Resellers" and self.instance == user
        )
        if condition:
            self.fields["role"] = forms.CharField(
                label="",
                widget=forms.HiddenInput(attrs={"class": "form-control"}),
                required=False
            )
        else:
            self.fields["role"].choices += (
                get_account_roles(user, self.instance)
                if self.instance.pk else get_account_roles(user)
            )

        if not user.is_superuser:
            del self.fields["master_user"]

        if not self.instance.pk:
            return

        domain_disabled = (
            hasattr(self.instance, "mailbox") and
            not self.instance.mailbox.domain.enabled
        )
        if domain_disabled:
            self.fields["is_active"].widget.attrs["disabled"] = "disabled"
        if args and domain_disabled:
            del self.fields["is_active"]
        self.fields["role"].initial = self.instance.role
        condition = (
            not self.instance.is_local and
            param_tools.get_global_parameter(
                "ldap_auth_method", app="core") == "directbind")
        if condition:
            del self.fields["random_password"]
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
        if self.user.role == "DomainAdmins":
            if self.instance == self.user:
                return "DomainAdmins"
            return "SimpleUsers"
        elif self.user.role == "Resellers" and self.instance == self.user:
            return "Resellers"
        return self.cleaned_data["role"]

    def clean_username(self):
        """username must be a valid email address for simple users."""
        username = self.cleaned_data["username"].lower()
        if "role" not in self.cleaned_data:
            return username
        if self.cleaned_data["role"] != "SimpleUsers" and "@" not in username:
            return username
        username = username.lower()
        validate_utf8_email(username)
        return username

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
        random_password = self.cleaned_data.get("random_password")
        if random_password:
            self.cleaned_data["password2"] = lib.make_password()
        elif "random_password" in self.fields and not random_password:
            password1 = self.cleaned_data.get("password1", "")
            password2 = self.cleaned_data.get("password2", "")
            empty_password = password1 == "" and password2 == ""
            if not self.instance.pk or not empty_password:
                if not password1:
                    self.add_error("password1", _("This field is required."))
                if not password2:
                    self.add_error("password2", _("This field is required."))
                if self.errors:
                    return self.cleaned_data
                if password1 != password2:
                    self.add_error(
                        "password2",
                        _("The two password fields didn't match."))
                    return self.cleaned_data
                try:
                    password_validation.validate_password(
                        password2, self.instance)
                except forms.ValidationError as ve:
                    self.add_error("password2", ve.messages)
        return self.cleaned_data

    def save(self, commit=True):
        account = super(AccountFormGeneral, self).save(commit=False)
        if self.user == account and not self.cleaned_data["is_active"]:
            raise lib_exceptions.PermDeniedException(
                _("You can't disable your own account"))
        if not account.pk:
            account.language = settings.LANGUAGE_CODE
        if commit:
            if self.cleaned_data.get("password2", "") != "":
                account.set_password(self.cleaned_data["password2"])
            account.save()
            account.role = self.cleaned_data["role"]
            if hasattr(account, "mailbox"):
                # Update forward status according to account status
                models.Alias.objects.filter(
                    address=account.email, internal=False).update(
                        enabled=account.is_active)
        return account


class AccountProfileForm(forms.ModelForm):
    """Form to edit account profile."""

    class Meta:
        model = User
        fields = ("secondary_email", "phone_number", "language")


class AccountFormMail(forms.Form, DynamicForm):
    """Form to handle mail part."""

    email = lib_fields.UTF8EmailField(
        label=ugettext_lazy("E-mail"), required=False)
    create_alias_with_old_address = forms.BooleanField(
        label=ugettext_lazy("Create an alias using the old address"),
        required=False,
        initial=False
    )
    quota = forms.CharField(
        label=ugettext_lazy("Quota"),
        required=False,
        help_text=_(
            "Quota for this mailbox, can be expressed in KB, MB (default) or "
            "GB. Define a custom value or "
            "use domain's default one. Leave empty to define an "
            "unlimited value (not allowed for domain "
            "administrators)."
        ),
        widget=forms.widgets.TextInput(attrs={"class": "form-control"})
    )
    quota_act = forms.BooleanField(required=False)
    message_limit = forms.IntegerField(
        label=ugettext_lazy("Message sending limit"),
        required=False,
        min_value=0,
        help_text=ugettext_lazy(
            "Number of messages this mailbox can send per day")
    )
    aliases = lib_fields.UTF8AndEmptyUserEmailField(
        label=ugettext_lazy("Alias(es)"),
        required=False,
        help_text=ugettext_lazy(
            "Alias(es) of this mailbox. Indicate only one address per input, "
            "press ENTER to add a new input. To create a catchall alias, just "
            "enter the domain name (@domain.tld)."
        )
    )
    senderaddress = lib_fields.UTF8AndEmptyUserEmailField(
        label=ugettext_lazy("Sender addresses"),
        required=False,
        help_text=ugettext_lazy(
            "Additional sender address(es) for this account. The user will be "
            "allowed to send emails using this address, even if it "
            "does not exist locally. Indicate one address per input. Press "
            "ENTER to add a new input."
        )
    )

    def __init__(self, user, *args, **kwargs):
        self.mb = kwargs.pop("instance", None)
        self.user = user
        super().__init__(*args, **kwargs)
        self.field_widths = {
            "quota": 3
        }
        params = dict(param_tools.get_global_parameters("admin"))
        if self.mb is not None:
            self.fields["email"].required = True
            qset = self.mb.aliasrecipient_set.filter(alias__internal=False)
            for cpt, ralias in enumerate(qset):
                name = "aliases_{}".format(cpt + 1)
                self._create_field(
                    lib_fields.UTF8AndEmptyUserEmailField, name,
                    ralias.alias.address)
            for cpt, saddress in enumerate(self.mb.senderaddress_set.all()):
                name = "senderaddress_{}".format(cpt + 1)
                self._create_field(
                    lib_fields.UTF8AndEmptyUserEmailField, name,
                    saddress.address)
            self.fields["email"].initial = self.mb.full_address
            self.fields["quota_act"].initial = self.mb.use_domain_quota
            if not self.mb.use_domain_quota and self.mb.quota:
                self.fields["quota"].initial = self.mb.quota
            if self.mb.message_limit:
                self.fields["message_limit"].initial = self.mb.message_limit
            self.fields["create_alias_with_old_address"].initial = (
                params["create_alias_on_mbox_rename"]
            )
        else:
            del self.fields["create_alias_with_old_address"]
            self.fields["quota_act"].initial = True
            if params["default_mailbox_message_limit"] is not None:
                self.fields["message_limit"].initial = (
                    params["default_mailbox_message_limit"])

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(
                args[0], "aliases", lib_fields.UTF8AndEmptyUserEmailField)
            self._load_from_qdict(
                args[0], "senderaddress",
                lib_fields.UTF8AndEmptyUserEmailField)

    def clean_email(self):
        """Ensure lower case emails"""
        email = self.cleaned_data["email"].lower()
        self.locpart, domname = split_mailbox(email)
        if not domname:
            return email
        try:
            self.domain = models.Domain.objects.get(name=domname)
        except models.Domain.DoesNotExist:
            raise forms.ValidationError(_("Domain does not exist"))
        if not self.mb:
            try:
                core_signals.can_create_object.send(
                    sender=self.__class__, context=self.domain,
                    object_type="mailboxes")
            except lib_exceptions.ModoboaException as inst:
                raise forms.ValidationError(inst)
        return email

    def clean_quota(self):
        """Convert quota to Bytes."""
        return size2integer(self.cleaned_data["quota"], output_unit="MB")

    def clean(self):
        """Custom fields validation.

        Check if quota is >= 0 only when the domain value is not used.
        """
        cleaned_data = super(AccountFormMail, self).clean()
        use_default_domain_quota = cleaned_data["quota_act"]
        condition = (
            not use_default_domain_quota and
            cleaned_data["quota"] is not None and
            cleaned_data["quota"] < 0)
        if condition:
            self.add_error("quota", _("Must be a positive integer"))
        self.aliases = []
        self.sender_addresses = []
        for name, value in list(cleaned_data.items()):
            if value == "":
                continue
            if name.startswith("aliases"):
                local_part, domname = split_mailbox(value)
                domain = models.Domain.objects.filter(name=domname).first()
                if not domain:
                    self.add_error(name, _("Local domain does not exist"))
                    continue
                if not self.user.can_access(domain):
                    self.add_error(
                        name, _("You don't have access to this domain"))
                    continue
                self.aliases.append(value.lower())
            elif name.startswith("senderaddress"):
                local_part, domname = split_mailbox(value)
                domain = models.Domain.objects.filter(name=domname).first()
                if domain and not self.user.can_access(domain):
                    self.add_error(
                        name, _("You don't have access to this domain"))
                    continue
                self.sender_addresses.append(value.lower())
        return cleaned_data

    def create_mailbox(self, user, account):
        """Create a mailbox associated to :kw:`account`."""
        if not user.can_access(self.domain):
            raise lib_exceptions.PermDeniedException
        core_signals.can_create_object.send(
            self.__class__, context=user, klass=models.Mailbox)
        self.mb = models.Mailbox(
            address=self.locpart, domain=self.domain, user=account,
            use_domain_quota=self.cleaned_data["quota_act"],
            message_limit=self.cleaned_data.get("message_limit")
        )
        override_rules = (
            user.is_superuser or
            user.has_perm("admin.add_domain") and
            not user.userobjectlimit_set.get(name="quota").max_value
        )
        self.mb.set_quota(self.cleaned_data["quota"], override_rules)
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
            self.__class__, context=user, klass=models.Alias,
            count=len(self.aliases))
        core_signals.can_create_object.send(
            self.__class__, context=self.mb.domain,
            object_type="mailbox_aliases", count=len(self.aliases))
        for alias in self.aliases:
            if self.mb.aliasrecipient_set.select_related("alias").filter(
                    alias__address=alias).exists():
                continue
            local_part, domname = split_mailbox(alias)
            al = models.Alias(address=alias, enabled=account.is_active)
            al.domain = models.Domain.objects.get(name=domname)
            al.save()
            al.set_recipients([self.mb.full_address])
            al.post_create(user)

    def _update_sender_addresses(self):
        """Update mailbox sender addresses."""
        for saddress in self.mb.senderaddress_set.all():
            if saddress.address not in self.sender_addresses:
                saddress.delete()
            else:
                self.sender_addresses.remove(saddress.address)
        if not len(self.sender_addresses):
            return
        to_create = []
        for saddress in self.sender_addresses:
            to_create.append(
                models.SenderAddress(address=saddress, mailbox=self.mb))
        models.SenderAddress.objects.bulk_create(to_create)

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
            if self.cleaned_data.get("create_alias_with_old_address", False):
                self.aliases.append(self.mb.full_address)
            self.mb.update_from_dict(user, self.cleaned_data)

        account.email = self.cleaned_data["email"]
        account.save()

        self._update_aliases(user, account)
        self._update_sender_addresses()

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
        qset = models.Domain.objects.get_for_admin(self.account)
        for pos, dom in enumerate(qset):
            name = "domains_%d" % (pos + 1)
            self._create_field(lib_fields.DomainNameField, name, dom.name)
        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(
                args[0], "domains", lib_fields.DomainNameField)

    def save(self):
        if self.account.role == "SimpleUsers":
            return
        current_domains = [
            dom.name for dom in
            models.Domain.objects.get_for_admin(self.account)
        ]
        for name, value in self.cleaned_data.items():
            if not name.startswith("domains"):
                continue
            if value in ["", None]:
                continue
            if value not in current_domains:
                domain = models.Domain.objects.get(name=value)
                domain.add_admin(self.account)

        for domain in models.Domain.objects.get_for_admin(self.account):
            if domain.name not in self.cleaned_data.values():
                domain.remove_admin(self.account)


class AccountForm(TabForms):
    """Account edition form."""

    def __init__(self, request, *args, **kwargs):
        self.user = request.user
        self.forms = [
            {"id": "general", "title": _("General"),
             "formtpl": "admin/account_general_form.html",
             "cls": AccountFormGeneral,
             "new_args": [self.user], "mandatory": True},
            {"id": "profile", "title": _("Profile"),
             "formtpl": "admin/account_profile_form.html",
             "cls": AccountProfileForm},
            {"id": "mail",
             "title": _("Mail"), "formtpl": "admin/mailform.html",
             "cls": AccountFormMail,
             "new_args": [self.user]},
            {"id": "perms", "title": _("Permissions"),
             "formtpl": "admin/permsform.html",
             "cls": AccountPermissionsForm}
        ]
        cbargs = {"user": self.user}
        if "instances" in kwargs:
            cbargs["account"] = kwargs["instances"]["general"]
        results = signals.extra_account_forms.send(
            sender=self.__class__, **cbargs)
        self.forms += reduce(
            lambda a, b: a + b, [result[1] for result in results])
        super(AccountForm, self).__init__(request, *args, **kwargs)

    def extra_context(self, context):
        account = self.instances["general"]
        context.update({
            "title": account.username,
            "formid": "accountform",
            "action": reverse("admin:account_change",
                              args=[account.id]),
        })

    def check_perms(self, account):
        """Check if perms form must displayed or not."""
        return (
            self.user.is_superuser and
            not account.is_superuser and
            account.has_perm("core.add_user")
        )

    def _before_is_valid(self, form):
        if form["id"] == "general":
            return True

        if hasattr(self, "check_%s" % form["id"]):
            if not getattr(self, "check_%s" % form["id"])(self.account):
                return False
            return True

        results = signals.check_extra_account_form.send(
            sender=self.__class__, account=self.account, form=form)
        results = [result[1] for result in results]
        if False in results:
            return False
        return True

    def is_valid(self):
        """Two steps validation."""
        self.instances["general"].oldgroup = self.instances["general"].role
        if super(AccountForm, self).is_valid(mandatory_only=True):
            self.account = self.forms[0]["instance"].save()
            return super(AccountForm, self).is_valid(optional_only=True)
        return False

    def save(self):
        """Custom save method

        As forms interact with each other, it is simpler to make
        custom code to save them.
        """
        self.forms[1]["instance"].save()
        self.forms[2]["instance"].save(self.user, self.account)
        if len(self.forms) <= 3:
            return
        for f in self.forms[3:]:
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
                "admin/mailform.html",
                new_args=[request.user]
            )
        )

    def extra_context(self, context):
        context.update({
            "title": _("New account"),
            "action": reverse("admin:account_add"),
            "formid": "newaccount_form"
        })

    def done(self):
        account = self.first_step.form.save()
        account.post_create(self.request.user)
        mailform = self.steps[1].form
        mailform.save(self.request.user, account)
        return render_to_json_response(_("Account created"))

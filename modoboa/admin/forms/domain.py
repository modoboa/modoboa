"""Forms related to domains management."""

from functools import reduce

from django import forms
from django.http import QueryDict
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.core import signals as core_signals
from modoboa.core.models import User
from modoboa.lib.exceptions import Conflict
from modoboa.lib.fields import DomainNameField
from modoboa.lib.form_utils import (
    DynamicForm, TabForms, WizardForm, WizardStep, YesNoField
)
from modoboa.lib.web_utils import render_to_json_response, size2integer
from modoboa.parameters import tools as param_tools
from .. import constants, lib, signals
from ..models import Alias, Domain, DomainAlias, Mailbox


class DomainFormGeneral(forms.ModelForm, DynamicForm):
    """A form to create/edit a domain."""

    type = forms.ChoiceField(  # NOQA:A003
        label=ugettext_lazy("Type"),
    )
    aliases = DomainNameField(
        label=ugettext_lazy("Alias(es)"),
        required=False,
        help_text=ugettext_lazy(
            "Alias(es) of this domain. Indicate only one name per input, "
            "press ENTER to add a new input."
        )
    )
    dkim_key_selector = forms.CharField(
        label=ugettext_lazy("Key selector"), initial="modoboa", required=False)
    quota = forms.CharField(
        label=ugettext_lazy("Quota"),
        initial=0,
        help_text=ugettext_lazy(
            "Quota shared between mailboxes. Can be expressed in KB, "
            "MB (default) or GB. A value of 0 means no quota."
        )
    )
    default_mailbox_quota = forms.CharField(
        label=ugettext_lazy("Default mailbox quota"),
        initial=0,
        help_text=ugettext_lazy(
            "Default quota applied to mailboxes. Can be expressed in KB, MB "
            "(default) or GB. A value of 0 means no quota."
        )
    )

    class Meta:
        model = Domain
        fields = (
            "name", "type", "quota", "default_mailbox_quota", "message_limit",
            "aliases", "enabled", "enable_dns_checks", "enable_dkim",
            "dkim_key_selector", "dkim_key_length"
        )

    def __init__(self, user, *args, **kwargs):
        self.oldname = None
        if "instance" in kwargs:
            self.old_dkim_key_length = kwargs["instance"].dkim_key_length
            self.oldname = kwargs["instance"].name
        super(DomainFormGeneral, self).__init__(*args, **kwargs)
        params = dict(param_tools.get_global_parameters("admin"))
        self.fields["quota"].initial = params["default_domain_quota"]
        if params["default_domain_message_limit"] is not None:
            self.fields["message_limit"].initial = (
                params["default_domain_message_limit"])
        self.fields["default_mailbox_quota"].initial = (
            params["default_mailbox_quota"])
        self.fields["type"].choices = constants.DOMAIN_TYPES
        self.field_widths = {
            "quota": 3,
            "default_mailbox_quota": 3
        }
        self.user = user

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "aliases", DomainNameField)
        elif "instance" in kwargs:
            d = kwargs["instance"]
            for pos, dalias in enumerate(d.domainalias_set.all()):
                name = "aliases_%d" % (pos + 1)
                self._create_field(forms.CharField, name, dalias.name, 3)

    def clean_name(self):
        """Check unicity and more."""
        name = self.cleaned_data["name"].lower()
        label = lib.check_if_domain_exists(
            name, [(DomainAlias, _("domain alias"))])
        if label is not None:
            raise forms.ValidationError(
                _("A %s with this name already exists") % force_text(label))

        domains_must_have_authorized_mx = (
            param_tools.get_global_parameter("domains_must_have_authorized_mx")
        )
        if domains_must_have_authorized_mx and not self.user.is_superuser:
            if not lib.domain_has_authorized_mx(name):
                raise forms.ValidationError(
                    _("No authorized MX record found for this domain"))

        return name

    def clean_enable_dkim(self):
        """Check prerequisites."""
        enabled = self.cleaned_data.get("enable_dkim")
        if not enabled:
            return enabled
        storage_dir = param_tools.get_global_parameter("dkim_keys_storage_dir")
        if not storage_dir:
            raise forms.ValidationError(
                _("DKIM keys storage directory not configured"))
        return enabled

    def clean_quota(self):
        """Return proper quota value."""
        return size2integer(self.cleaned_data["quota"], output_unit="MB")

    def clean_default_mailbox_quota(self):
        """Return proper quota value."""
        return size2integer(
            self.cleaned_data["default_mailbox_quota"], output_unit="MB")

    def clean(self):
        """Custom fields validation.

        We want to prevent duplicate names between domains and domain
        aliases.

        The validation way is not very smart...
        """
        cleaned_data = super(DomainFormGeneral, self).clean()
        if self._errors:
            return cleaned_data
        condition = (
            self.cleaned_data["quota"] != 0 and
            self.cleaned_data["default_mailbox_quota"] >
            self.cleaned_data["quota"])
        if condition:
            self.add_error(
                "default_mailbox_quota",
                _("Cannot be greater than domain quota"))
        elif self.user.role == "Resellers":
            limit = self.user.userobjectlimit_set.get(name="quota")
            if limit.max_value != 0:
                quota = self.cleaned_data["quota"]
                msg = _("You can't define an unlimited quota.")
                if quota == 0:
                    self.add_error("quota", msg)
                default_mailbox_quota = self.cleaned_data[
                    "default_mailbox_quota"]
                if default_mailbox_quota == 0:
                    self.add_error("default_mailbox_quota", msg)
        if self.cleaned_data["enable_dkim"]:
            if not self.cleaned_data.get("dkim_key_selector"):
                self.add_error(
                    "dkim_key_selector", _("This field is required."))
        self.aliases = []
        copied_data = cleaned_data.copy()
        for k in copied_data.keys():
            if not k.startswith("aliases"):
                continue
            if cleaned_data[k] == "":
                del cleaned_data[k]
                continue
            if cleaned_data[k] == self.cleaned_data["name"]:
                self._errors[k] = self.error_class(
                    [_("A %s with this name already exists") % _("domain")]
                )
                del cleaned_data[k]
                continue
            label = lib.check_if_domain_exists(
                cleaned_data[k], [(Domain, _("domain"))])
            if label is not None:
                self.add_error(
                    k, _("A %s with this name already exists")
                    % force_text(label)
                )
            else:
                self.aliases.append(cleaned_data[k])
        return cleaned_data

    def save(self, user, commit=True, domalias_post_create=False):
        """Custom save method.

        Updating a domain may have consequences on other objects
        (domain alias, mailbox, quota). The most tricky part concerns
        quotas update.

        """
        d = super(DomainFormGeneral, self).save(commit=False)
        core_signals.can_create_object.send(
            sender=self.__class__, context=user, klass=Domain, instance=d)
        if not commit:
            return d
        d.save()
        for dalias in d.domainalias_set.all():
            if dalias.name not in self.aliases:
                dalias.delete()
            else:
                self.aliases.remove(dalias.name)
        if self.aliases:
            core_signals.can_create_object.send(
                self.__class__, context=user, klass=DomainAlias,
                count=len(self.aliases))
            core_signals.can_create_object.send(
                self.__class__, context=d, object_type="domain_aliases",
                count=len(self.aliases))
            for alias in self.aliases:
                if d.domainalias_set.filter(name=alias).exists():
                    continue
                options = {"creator": user} if domalias_post_create else {}
                DomainAlias(name=alias, target=d, enabled=d.enabled).save(
                    **options)
        return d


class DomainFormOptions(forms.Form):
    """A form containing options for domain creation."""

    create_dom_admin = YesNoField(
        label=ugettext_lazy("Create a domain administrator"),
        initial=False,
        help_text=ugettext_lazy(
            "Automatically create an administrator for this domain"
        )
    )

    dom_admin_username = forms.CharField(
        label=ugettext_lazy("Name"),
        initial="admin",
        help_text=ugettext_lazy(
            "The administrator's name. Don't include the domain's name here, "
            "it will be automatically appended."
        ),
        required=False
    )

    random_password = YesNoField(
        label=ugettext_lazy("Random password"),
        initial=False,
        help_text=ugettext_lazy(
            "Generate a random password for the administrator."
        ),
        required=False
    )

    with_mailbox = YesNoField(
        label=ugettext_lazy("With a mailbox"),
        initial=True,
        help_text=ugettext_lazy(
            "Create a mailbox for the administrator."
        ),
        required=False
    )

    create_aliases = YesNoField(
        label=ugettext_lazy("Create aliases"),
        initial=True,
        help_text=ugettext_lazy(
            "Automatically create standard aliases for this domain"
        ),
        required=False
    )

    def __init__(self, user, *args, **kwargs):
        super(DomainFormOptions, self).__init__(*args, **kwargs)
        results = core_signals.user_can_set_role.send(
            sender=self.__class__, user=user, role="DomainAdmins")
        if False in [result[1] for result in results]:
            self.fields = {}
            return

    def clean_dom_admin_username(self):
        """Ensure admin username is an email address."""
        if "@" in self.cleaned_data["dom_admin_username"]:
            raise forms.ValidationError(_("Invalid format"))
        return self.cleaned_data["dom_admin_username"]

    def clean(self):
        """Check required values."""
        cleaned_data = super(DomainFormOptions, self).clean()
        if cleaned_data.get("create_dom_admin"):
            if not cleaned_data.get("dom_admin_username"):
                self.add_error(
                    "dom_admin_username", _("This field is required."))
            if "create_aliases" not in cleaned_data:
                self.add_error(
                    "create_aliases", _("This field is required."))
        return cleaned_data

    def save(self, *args, **kwargs):
        if not self.fields:
            return
        if not self.cleaned_data["create_dom_admin"]:
            return
        user = kwargs.pop("user")
        domain = kwargs.pop("domain")
        username = "%s@%s" % (
            self.cleaned_data["dom_admin_username"], domain.name)
        try:
            da = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        else:
            raise Conflict(_("User '%s' already exists") % username)
        core_signals.can_create_object.send(
            self.__class__, context=user, klass=Mailbox)
        da = User(username=username, email=username, is_active=True)
        if self.cleaned_data["random_password"]:
            password = lib.make_password()
        else:
            password = param_tools.get_global_parameter(
                "default_password", app="core")
        da.set_password(password)
        da.save()
        da.role = "DomainAdmins"
        da.post_create(user)

        if self.cleaned_data["with_mailbox"]:
            dom_admin_username = self.cleaned_data["dom_admin_username"]
            mb = Mailbox(
                address=dom_admin_username, domain=domain,
                user=da, use_domain_quota=True
            )
            mb.set_quota(
                override_rules=user.has_perm("admin.change_domain"))
            mb.save(creator=user)

            condition = (
                domain.type == "domain" and
                self.cleaned_data["create_aliases"] and
                dom_admin_username != "postmaster"
            )
            if condition:
                core_signals.can_create_object.send(
                    self.__class__, context=user, klass=Alias)
                address = u"postmaster@{}".format(domain.name)
                alias = Alias.objects.create(
                    address=address, domain=domain, enabled=True)
                alias.set_recipients([mb.full_address])
                alias.post_create(user)

        domain.add_admin(da)


class DomainForm(TabForms):
    """Domain edition form."""

    def __init__(self, request, *args, **kwargs):
        self.user = request.user
        self.forms = []
        self.domain = None
        if self.user.has_perm("admin.change_domain"):
            self.forms.append({
                "id": "general",
                "title": _("General"),
                "formtpl": "admin/domain_general_form.html",
                "cls": DomainFormGeneral,
                "mandatory": True,
                "new_args": [request.user]
            })

        cbargs = {"user": self.user}
        if "instances" in kwargs:
            self.domain = kwargs["instances"]["general"]
            cbargs["domain"] = self.domain
        results = signals.extra_domain_forms.send(
            sender=self.__class__, **cbargs)
        self.forms += reduce(
            lambda a, b: a + b, [result[1] for result in results])
        if not self.forms:
            self.active_id = "admins"
        super(DomainForm, self).__init__(request, *args, **kwargs)

    def extra_context(self, context):
        """Add information to template context."""
        context.update({
            "title": self.domain.name,
            "action": reverse(
                "admin:domain_change", args=[self.domain.pk]),
            "formid": "domform",
            "domain": self.domain
        })

    def is_valid(self):
        """Custom validation.

        We just save the current name before it is potentially
        modified.

        """
        if "general" in self.instances:
            instance = self.instances["general"]
            instance.oldname = instance.name
        return super(DomainForm, self).is_valid()

    def save(self):
        """Custom save method.

        As forms interact with each other, it is easier to make custom
        code to save them.
        """
        if not self.forms:
            return
        first_form = self.forms[0]["instance"]
        options = {}
        if isinstance(first_form, DomainFormGeneral):
            domain = first_form.save(
                self.request.user, domalias_post_create=True)
            options.update({"domain": domain})
        else:
            first_form.save(self.request.user)
        for f in self.forms[1:]:
            f["instance"].save(self.request.user, **options)

    def done(self):
        return render_to_json_response(_("Domain modified"))


class DomainWizard(WizardForm):
    """Domain creation wizard."""

    def __init__(self, request):
        super(DomainWizard, self).__init__(request)
        self.add_step(
            WizardStep(
                "general", DomainFormGeneral, _("General"),
                "admin/domain_general_form.html",
                [request.user]
            )
        )
        results = signals.extra_domain_wizard_steps.send(sender=self.__class__)
        for result in results:
            for step in result[1]:
                self.add_step(step)
        self.add_step(
            WizardStep(
                "options", DomainFormOptions, _("Options"),
                "admin/domain_options_form.html",
                [self.request.user]
            )
        )

    def extra_context(self, context):
        context.update({
            "title": _("New domain"),
            "action": reverse("admin:domain_add"),
            "formid": "domform"
        })

    def done(self):
        genform = self.first_step.form
        domain = genform.save(self.request.user)
        domain.post_create(self.request.user)
        for step in self.steps[1:]:
            if not step.check_access(self):
                continue
            step.form.save(user=self.request.user, domain=domain)
        return render_to_json_response(_("Domain created"))

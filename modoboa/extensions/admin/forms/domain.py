from django import forms
from django.http import QueryDict
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse

from modoboa.lib import events, parameters
from modoboa.lib.exceptions import ModoboaException, Conflict
from modoboa.lib.formutils import (
    DomainNameField, YesNoField, WizardForm, DynamicForm, TabForms
)
from modoboa.lib.webutils import render_to_json_response
from modoboa.core.models import User
from modoboa.extensions.admin.lib import check_if_domain_exists
from modoboa.extensions.admin.models import (
    Domain, DomainAlias, Mailbox, Alias, Quota
)


class DomainFormGeneral(forms.ModelForm, DynamicForm):
    quota = forms.IntegerField(
        label=ugettext_lazy("Quota"),
        required=False,
        help_text=ugettext_lazy(
            "Default quota in MB applied to mailboxes. Leave empty to use the "
            "default value."
        )
    )
    aliases = DomainNameField(
        label=ugettext_lazy("Alias(es)"),
        required=False,
        help_text=ugettext_lazy(
            "Alias(es) of this domain. Indicate only one name per input, "
            "press ENTER to add a new input."
        )
    )
    name = DomainNameField(
        widget=forms.TextInput()
    )

    class Meta:
        model = Domain
        fields = ("name", "quota", "aliases", "enabled")

    def __init__(self, *args, **kwargs):
        self.oldname = None
        if "instance" in kwargs:
            self.oldname = kwargs["instance"].name
        super(DomainFormGeneral, self).__init__(*args, **kwargs)

        self.field_widths = {
            "quota": 3
        }

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "aliases", DomainNameField)
        elif "instance" in kwargs:
            d = kwargs["instance"]
            for pos, dalias in enumerate(d.domainalias_set.all()):
                name = "aliases_%d" % (pos + 1)
                self._create_field(forms.CharField, name, dalias.name, 3)

    def clean_quota(self):
        if self.cleaned_data['quota'] is None:
            return int(parameters.get_admin('DEFAULT_DOMAIN_QUOTA'))
        if self.cleaned_data['quota'] < 0:
            raise forms.ValidationError(_("Must be a positive integer"))
        return self.cleaned_data['quota']

    def clean(self):
        """Custom fields validation.

        We want to prevent duplicate names between domains and domain
        aliases. Extensions have the possibility to declare other
        objects (see *CheckDomainName* event).

        The validation way is not very smart...
        """
        super(DomainFormGeneral, self).clean()
        if self._errors:
            raise forms.ValidationError(self._errors)

        cleaned_data = self.cleaned_data
        name = cleaned_data["name"]
        label = check_if_domain_exists(name, [(DomainAlias, _('domain alias'))])
        if label is not None:
            self._errors["name"] = self.error_class(
                [_("A %s with this name already exists" % unicode(label))]
            )
            del cleaned_data["name"]

        for k in cleaned_data.keys():
            if not k.startswith("aliases"):
                continue
            if cleaned_data[k] == "":
                del cleaned_data[k]
                continue
            if cleaned_data[k] == name:
                self._errors[k] = self.error_class(
                    [_("A %s with this name already exists") % _("domain")]
                )
                del cleaned_data[k]
                continue
            label = check_if_domain_exists(
                cleaned_data[k], [(Domain, _("domain"))])
            if label is not None:
                self._errors[k] = self.error_class(
                    [_("A %s with this name already exists" % unicode(label))]
                )
                del cleaned_data[k]

        return cleaned_data

    def update_mailbox_quotas(self, domain):
        """Update all quota records associated to this domain.

        This method must be called only when a domain gets renamed. As
        the primary key used for a quota is an email address, rename a
        domain will change all associated email addresses, so it will
        change the primary keys used for quotas. The consequence is we
        can't issue regular UPDATE queries using the .save() method of
        a Quota instance (it will trigger an INSERT as the primary key
        has changed).

        So, we use this ugly hack to bypass this behaviour. It is not
        perfomant at all as it will generate one query per quota
        record to update.
        """
        for q in Quota.objects.filter(username__contains="@%s" % self.oldname):
            username = q.username.replace(
                '@%s' % self.oldname, '@%s' % domain.name)
            newq = Quota.objects.create(
                username=username, bytes=q.bytes, messages=q.messages)
            q.delete()

    def save(self, user, commit=True, domalias_post_create=False):
        """Custom save method

        Updating a domain may have consequences on other objects
        (domain alias, mailbox, quota). The most tricky part concerns
        quotas update.

        """
        d = super(DomainFormGeneral, self).save(commit=False)
        if commit:
            old_mail_homes = None
            if self.oldname is not None and d.name != self.oldname:
                d.name = self.oldname
                old_mail_homes = \
                    dict((mb.id, mb.mail_home) for mb in d.mailbox_set.all())
                d.name = self.cleaned_data['name']
            d.save()
            Mailbox.objects.filter(domain=d, use_domain_quota=True) \
                .update(quota=d.quota)
            aliases = []
            for k, v in self.cleaned_data.iteritems():
                if not k.startswith("aliases"):
                    continue
                if v in ["", None]:
                    continue
                aliases.append(v)
            for dalias in d.domainalias_set.all():
                if not dalias.name in aliases:
                    dalias.delete()
                else:
                    aliases.remove(dalias.name)
            if aliases:
                events.raiseEvent("CanCreate", user, "domain_aliases", len(aliases))
                for alias in aliases:
                    try:
                        d.domainalias_set.get(name=alias)
                    except DomainAlias.DoesNotExist:
                        pass
                    else:
                        continue
                    al = DomainAlias(name=alias, target=d, enabled=d.enabled)
                    al.save(creator=user) if domalias_post_create else al.save()

            if old_mail_homes is not None:
                self.update_mailbox_quotas(d)
                for mb in d.mailbox_set.all():
                    mb.rename_dir(old_mail_homes[mb.id])

        return d


class DomainFormOptions(forms.Form):
    create_dom_admin = YesNoField(
        label=ugettext_lazy("Create a domain administrator"),
        initial="no",
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

    create_aliases = YesNoField(
        label=ugettext_lazy("Create aliases"),
        initial="yes",
        help_text=ugettext_lazy(
            "Automatically create standard aliases for this domain"
        ),
        required=False
    )

    def __init__(self, user, *args, **kwargs):
        super(DomainFormOptions, self).__init__(*args, **kwargs)
        if False in events.raiseQueryEvent('UserCanSetRole', user, 'DomainAdmins'):
            self.fields = {}
            return
        if args:
            if args[0].get("create_dom_admin", "no") == "yes":
                self.fields["dom_admin_username"].required = True
                self.fields["create_aliases"].required = True

    def clean_dom_admin_username(self):
        """Ensure admin username is an email address."""
        if '@' in self.cleaned_data["dom_admin_username"]:
            raise forms.ValidationError(_("Invalid format"))
        return self.cleaned_data["dom_admin_username"]

    def save(self, user, domain):
        if not self.fields:
            return
        if self.cleaned_data["create_dom_admin"] == "no":
            return
        username = "%s@%s" % (
            self.cleaned_data["dom_admin_username"], domain.name)
        try:
            da = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        else:
            raise Conflict(_("User '%s' already exists" % username))
        events.raiseEvent("CanCreate", user, "mailboxes")
        da = User(username=username, email=username, is_active=True)
        da.set_password("password")
        da.save()
        da.set_role("DomainAdmins")
        da.post_create(user)
        mb = Mailbox(
            address=self.cleaned_data["dom_admin_username"], domain=domain,
            user=da, use_domain_quota=True
        )
        mb.set_quota(override_rules=user.has_perm("admin.change_domain"))
        mb.save(creator=user)

        if self.cleaned_data["create_aliases"] == "yes":
            events.raiseEvent("CanCreate", user, "mailbox_aliases")
            alias = Alias(address="postmaster", domain=domain, enabled=True)
            alias.save(int_rcpts=[mb])
            alias.post_create(user)

        domain.add_admin(da)


class DomainForm(TabForms):

    """Domain edition form."""

    template_name = "admin/editdomainform.html"

    def __init__(self, request, *args, **kwargs):
        self.user = request.user
        self.domain = None
        self.forms = []
        if self.user.has_perm("admin.change_domain"):
            self.forms.append({
                "id": "general",
                "title": _("General"),
                "formtpl": "admin/domain_general_form.html",
                "cls": DomainFormGeneral,
                "mandatory": True
            })

        cbargs = [self.user]
        if "instances" in kwargs:
            self.domain = kwargs["instances"]["general"]
            cbargs += [self.domain]
        self.forms += events.raiseQueryEvent("ExtraDomainForm", *cbargs)
        if not self.forms:
            self.active_id = "admins"
        super(DomainForm, self).__init__(request, *args, **kwargs)

    def extra_context(self, context):
        domadmins = [u for u in self.domain.admins
                     if self.request.user.can_access(u) and not u.is_superuser]
        if not self.request.user.is_superuser:
            domadmins = [u for u in domadmins if u.group == "DomainAdmins"]
        context.update({
            "title": self.domain.name,
            "action": reverse(
                "admin:domain_change", args=[self.domain.pk]),
            "formid": "domform",
            "domain": self.domain,
            "domadmins": domadmins
        })

    def is_valid(self):
        """Custom validation.

        We just save the current name before it is potentially
        modified.

        """
        if "general" in self.instances:
            self.instances["general"].oldname = self.instances["general"].name
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
            options.update({"domalias_post_create": True})
        first_form.save(self.request.user, **options)
        for f in self.forms[1:]:
            f["instance"].save(self.request.user)

    def done(self):
        if "general" in self.instances:
            events.raiseEvent("DomainModified", self.instances["general"])
        return render_to_json_response(_("Domain modified"))


class DomainWizard(WizardForm):
    """Domain creation wizard.
    """
    def __init__(self, request):
        super(DomainWizard, self).__init__(request)
        self.add_step(
            DomainFormGeneral, _("General"),
            formtpl="admin/domain_general_form.html"
        )
        self.add_step(
            DomainFormOptions, _("Options"),
            formtpl="admin/domain_options_form.html",
            new_args=[self.request.user]
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
        try:
            self.steps[1].form.save(self.request.user, domain)
        except ModoboaException:
            from django.db import transaction
            transaction.rollback()
            raise
        return render_to_json_response(_("Domain created"))

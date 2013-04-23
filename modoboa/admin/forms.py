# coding: utf-8
from django import forms
from django.contrib.auth.models import Group
from modoboa.admin.models import *
from django.utils.translation import ugettext as _, ugettext_lazy
from django.http import QueryDict
from modoboa.admin.templatetags.admin_extras import gender
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.permissions import get_account_roles
from modoboa.lib.formutils import *
from modoboa.lib.permissions import *


class DomainFormGeneral(forms.ModelForm, DynamicForm):
    aliases = DomainNameField(
        label=ugettext_lazy("Alias(es)"),
        required=False,
        help_text=ugettext_lazy("Alias(es) of this domain. Indicate only one name per input, press ENTER to add a new input.")
    )

    class Meta:
        model = Domain
        fields = ("name", "quota", "aliases", "enabled")
        widgets = dict(
            quota=forms.widgets.TextInput(attrs={"class": "span1"})
        )

    def __init__(self, *args, **kwargs):
        self.oldname = None
        if "instance" in kwargs:
            self.oldname = kwargs["instance"].name
        super(DomainFormGeneral, self).__init__(*args, **kwargs)

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "aliases", DomainNameField)
        elif "instance" in kwargs:
            d = kwargs["instance"]
            for pos, dalias in enumerate(d.domainalias_set.all()):
                name = "aliases_%d" % (pos + 1)
                self._create_field(forms.CharField, name, dalias.name, 3)

    def clean(self):
        super(DomainFormGeneral, self).clean()
        if len(self._errors):
            raise forms.ValidationError(self._errors)

        cleaned_data = self.cleaned_data
        name = cleaned_data["name"]

        try:
            DomainAlias.objects.get(name=name)
        except DomainAlias.DoesNotExist:
            pass
        else:
            self._errors["name"] = self.error_class([_("An alias with this name already exists")])
            del cleaned_data["name"]

        errors = []
        for k in cleaned_data.keys():
            if not k.startswith("aliases"):
                continue
            if cleaned_data[k] == "":
                del cleaned_data[k]
                continue
            try:
                Domain.objects.get(name=cleaned_data[k])
            except Domain.DoesNotExist:
                pass
            else:
                self._errors[k] = self.error_class([_("A domain with this name already exists")])
                del cleaned_data[k]

        return cleaned_data

    def save(self, user, commit=True):
        d = super(DomainFormGeneral, self).save(commit=False)
        if commit:
            old_mail_homes = None
            hm = parameters.get_admin("HANDLE_MAILBOXES", raise_error=False)
            if hm == "yes":
                if self.oldname is not None and d.name != self.oldname:
                    for q in Quota.objects.filter(username__contains="@%s" % self.oldname):
                        q.username = q.username.replace('@%s' % self.oldname, '@%s' % d.name)
                        q.save()
                    old_mail_homes = dict((mb.id, mb.mail_home) for mb in d.mailbox_set.all())
            d.save()
            if old_mail_homes is not None:
                for mb in d.mailbox_set.all():
                    mb.rename_dir(old_mail_homes[mb.id])
            for k, v in self.cleaned_data.iteritems():
                if not k.startswith("aliases"):
                    continue
                if v in ["", None]:
                    continue
                try:
                    d.domainalias_set.get(name=v)
                except DomainAlias.DoesNotExist:
                    pass
                else:
                    continue
                events.raiseEvent("CanCreate", user, "domain_aliases")
                al = DomainAlias(name=v, target=d, enabled=d.enabled)
                al.save()
                grant_access_to_object(user, al, is_owner=True)
                events.raiseEvent("DomainAliasCreated", user, al)

            for dalias in d.domainalias_set.all():
                if not len(filter(lambda name: self.cleaned_data[name] == dalias.name,
                                  self.cleaned_data.keys())):
                    dalias.delete()
        return d


class DomainForm(TabForms):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.forms = []
        if user.has_perm("admin.change_domain"):
            self.forms.append(dict(
                id="general", title=_("General"), formtpl="admin/domain_general_form.html",
                cls=DomainFormGeneral, mandatory=True
            ))

        cbargs = [user]
        if "instances" in kwargs:
            cbargs += [kwargs["instances"]["general"]]
        self.forms += events.raiseQueryEvent("ExtraDomainForm", *cbargs)

        super(DomainForm, self).__init__(*args, **kwargs)

    def save(self, user):
        """Custom save method

        As forms interact with each other, it is easier to make custom
        code to save them.
        """
        for f in self.forms:
            f["instance"].save(user)


class DlistForm(forms.ModelForm, DynamicForm):
    email = forms.EmailField(
        label=ugettext_lazy("Email address"),
        help_text=ugettext_lazy("The distribution list address. Use the '*' character to create a 'catchall' address (ex: *@domain.tld).")
    )
    recipients = forms.EmailField(
        label=ugettext_lazy("Recipients"), required=False,
        help_text=ugettext_lazy("Mailbox(es) this alias will point to. Indicate only one address per input, press ENTER to add a new input.")
    )

    class Meta:
        model = Alias
        fields = ("enabled",)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(DlistForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['email', 'recipients', 'enabled']

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "recipients", forms.EmailField)
        elif "instance" in kwargs:
            dlist = kwargs["instance"]
            self.fields["email"].initial = dlist.full_address
            cpt = 1
            for mb in dlist.mboxes.all():
                name = "recipients_%d" % (cpt)
                self._create_field(forms.EmailField, name, mb.full_address, 2)
                cpt += 1
            for addr in dlist.extmboxes.split(','):
                if addr == "":
                    continue
                name = "recipients_%d" % (cpt)
                self._create_field(forms.EmailField, name, addr, 2)
                cpt += 1

    def clean_email(self):
        localpart, domname = split_mailbox(self.cleaned_data["email"])
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise forms.ValidationError(_("Domain does not exist"))
        if not self.user.can_access(domain):
            raise forms.ValidationError(_("You don't have access to this domain"))
        return self.cleaned_data["email"]

    def set_recipients(self):
        """Recipients dispatching

        We make a difference between 'local' recipients (the ones hosted
        by Modoboa) and 'external' recipients.
        """
        self.ext_rcpts = []
        self.int_rcpts = []
        total = 0

        for k, v in self.cleaned_data.iteritems():
            if not k.startswith("recipients"):
                continue
            if v == "":
                continue
            local_part, domname = split_mailbox(v)
            if domname is None:
                raise AdminError("%s %s" % (_("Invalid mailbox"), v))
            try:
                domain = Domain.objects.get(name=domname)
            except Domain.DoesNotExist:
                domain = None
            if domain:
                if not self.user.can_access(domain):
                    raise PermDeniedException(v)
                try:
                    mb = Mailbox.objects.get(domain=domain, address=local_part)
                except Mailbox.DoesNotExist:
                    raise AdminError(_("Mailbox %s does not exist" % v))
                if mb in self.int_rcpts:
                    raise AdminError(_("Recipient %s already present" % v))
                self.int_rcpts += [mb]
                total += 1
                continue

            if v in self.ext_rcpts:
                raise AdminError(_("Recipient %s already present" % v))
            self.ext_rcpts += [v]
            total += 1

        if total == 0:
            raise AdminError(_("No recipient defined"))

        if total < 2:
            raise AdminError(_("A distribution list must contain at least two recipients"))

    def save(self, commit=True):
        dlist = super(DlistForm, self).save(commit=False)
        localpart, domname = split_mailbox(self.cleaned_data["email"])
        dlist.address = localpart
        dlist.domain = Domain.objects.get(name=domname)
        if commit:
            dlist.save(self.int_rcpts, self.ext_rcpts)
            self.save_m2m()
        return dlist


class GenericAliasForm(forms.ModelForm):
    email = forms.EmailField(
        label=ugettext_lazy("Address"),
        help_text=ugettext_lazy("A valid e-mail address. Use the '*' character to create a 'catchall' address (ex: *@domain.tld).")
    )

    class Meta:
        model = Alias
        fields = ("enabled", )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(GenericAliasForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            alias = kwargs["instance"]
            self.fields["email"].initial = alias.full_address

    def clean_email(self):
        localpart, domname = split_mailbox(self.cleaned_data["email"])
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise forms.ValidationError(_("Domain does not exist"))
        if not self.user.can_access(domain):
            raise forms.ValidationError(_("You don't have access to this domain"))
        return self.cleaned_data["email"]

    def set_recipients(self):
        pass

    def _save(self):
        alias = super(GenericAliasForm, self).save(commit=False)
        localpart, domname = split_mailbox(self.cleaned_data["email"])
        alias.address = localpart
        alias.domain = Domain.objects.get(name=domname)
        return alias


class AliasForm(GenericAliasForm):
    int_recipient = forms.EmailField(
        label=ugettext_lazy("Recipient"),
        help_text=ugettext_lazy("A local recipient address")
    )

    def __init__(self, *args, **kwargs):
        super(AliasForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['email', 'int_recipient', 'enabled']
        if "instance" in kwargs:
            alias = kwargs["instance"]
            if len(alias.mboxes.all()):
                self.fields["int_recipient"].initial = alias.mboxes.all()[0].full_address

    def clean_int_recipient(self):
        localpart, domname = split_mailbox(self.cleaned_data["int_recipient"])
        try:
            self.rcpt_mb = Mailbox.objects.get(address=localpart, domain__name=domname)
        except Mailbox.DoesNotExist:
            raise forms.ValidationError(_("Mailbox does not exist"))
        if not self.user.can_access(self.rcpt_mb):
            raise forms.ValidationError(_("You can't access this mailbox"))
        return self.cleaned_data["int_recipient"]

    def save(self, commit=True):
        alias = self._save()
        if commit:
            alias.save([self.rcpt_mb], [])
        return alias


class ForwardForm(GenericAliasForm):
    ext_recipient = forms.EmailField(
        label=ugettext_lazy("Recipient"),
        help_text=ugettext_lazy("An external recipient address")
    )

    def __init__(self, *args, **kwargs):
        super(ForwardForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['email', 'ext_recipient', 'enabled']
        if "instance" in kwargs:
            alias = kwargs["instance"]
            self.fields["ext_recipient"].initial = alias.extmboxes

    def clean_ext_recipient(self):
        local_part, domname = split_mailbox(self.cleaned_data["ext_recipient"])
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(_("Local recipients are forbidden"))
        return self.cleaned_data["ext_recipient"]

    def save(self, commit=True):
        alias = self._save()
        if commit:
            alias.save([], [self.cleaned_data["ext_recipient"]])
        return alias


class ImportDataForm(forms.Form):
    sourcefile = forms.FileField(label=ugettext_lazy("Select a file"))
    sepchar = forms.CharField(label=ugettext_lazy("Separator"), max_length=1, required=False)
    continue_if_exists = forms.BooleanField(
        label=ugettext_lazy("Continue on error"), required=False,
        help_text=ugettext_lazy("Don't treat duplicated objects as error")
    )

    def __init__(self, *args, **kwargs):
        super(ImportDataForm, self).__init__(*args, **kwargs)
        self.fields["sepchar"].widget.attrs = {"class": "span1"}

    def clean_sepchar(self):
        if self.cleaned_data["sepchar"] == "":
            return ";"
        return str(self.cleaned_data["sepchar"])


class ImportIdentitiesForm(ImportDataForm):
    crypt_password = forms.BooleanField(
        label=ugettext_lazy("Crypt passwords"), required=False,
        help_text=ugettext_lazy("Check this option if passwords contained in your file are not crypted")
    )


class ExportDataForm(forms.Form):
    filename = forms.CharField(
        label=ugettext_lazy("File name"), max_length=100, required=False
    )
    sepchar = forms.CharField(label=ugettext_lazy("Separator"), max_length=1, required=False)

    def __init__(self, *args, **kwargs):
        super(ExportDataForm, self).__init__(*args, **kwargs)
        self.fields["sepchar"].widget.attrs = {"class": "span1"}

    def clean_sepchar(self):
        if self.cleaned_data["sepchar"] == "":
            return ";"
        return str(self.cleaned_data["sepchar"])

    def clean_filename(self):
        if self.cleaned_data["filename"] == "":
            return self.fields["filename"].initial
        return str(self.cleaned_data["filename"])


class ExportDomainsForm(ExportDataForm):
    def __init__(self, *args, **kwargs):
        super(ExportDomainsForm, self).__init__(*args, **kwargs)
        self.fields["filename"].initial = "modoboa-domains.csv"


class ExportIdentitiesForm(ExportDataForm):
    def __init__(self, *args, **kwargs):
        super(ExportIdentitiesForm, self).__init__(*args, **kwargs)
        self.fields["filename"].initial = "modoboa-identities.csv"


class AccountFormGeneral(forms.ModelForm):
    username = forms.CharField(label=ugettext_lazy("Username"), max_length=254)
    role = forms.ChoiceField(
        label=ugettext_lazy("Role"),
        choices=[('', ugettext_lazy("Choose"))],
        help_text=ugettext_lazy("What level of permission this user will have")
    )
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=ugettext_lazy("Confirmation"),
        widget=forms.PasswordInput,
        help_text=ugettext_lazy("Enter the same password as above, for verification.")
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
            del self.fields["role"]
        else:
            self.fields["role"].choices = \
                [('', ugettext_lazy("Choose"))] + get_account_roles(user)

        if "instance" in kwargs:
            if len(args) \
               and (args[0].get("password1", "") == ""
               and args[0].get("password2", "") == ""):
                self.fields["password1"].required = False
                self.fields["password2"].required = False
            if user.group != "DomainAdmins":
                u = kwargs["instance"]
                if u.is_superuser:
                    role = "SuperAdmins"
                else:
                    try:
                        role = u.groups.all()[0].name
                    except IndexError:
                        pass
                self.fields["role"].initial = role

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

    def give_all_accesses(self, account):
        """Give access to all objects defined in the database

        Must be used when an account is promoted as a super user.

        :param account: a ``User`` instance
        """
        grant_access_to_objects(account, User.objects.all(), get_content_type(User))
        grant_access_to_objects(account, Domain.objects.all(), get_content_type(Domain))
        grant_access_to_objects(account, DomainAlias.objects.all(), get_content_type(DomainAlias))
        grant_access_to_objects(account, Mailbox.objects.all(), get_content_type(Mailbox))
        grant_access_to_objects(account, Alias.objects.all(), get_content_type(Alias))

    def save(self, commit=True):
        account = super(AccountFormGeneral, self).save(commit=False)
        if self.user == account and not self.cleaned_data["is_active"]:
            raise AdminError(_("You can't disable your own account"))
        if commit:
            if self.cleaned_data["password1"] != "":
                account.set_password(self.cleaned_data["password1"])
            account.save()
            role = None
            if "role" in self.cleaned_data:
                role = self.cleaned_data["role"]
            elif self.user.group == "DomainAdmins" and self.user != account:
                role = "SimpleUsers"

            if role is None or account.group == role:
                return account

            account.groups.clear()
            if role == "SuperAdmins":
                account.is_superuser = True
                self.give_all_accesses(account)
            else:
                if account.is_superuser:
                    ObjectAccess.objects.filter(user=account).delete()
                account.is_superuser = False
                account.groups.add(Group.objects.get(name=role))
            account.save()
        return account


class AccountFormMail(forms.Form, DynamicForm):
    email = forms.EmailField(label=ugettext_lazy("E-mail"), required=False)
    quota = forms.IntegerField(
        label=ugettext_lazy("Quota"),
        required=False,
        help_text=_("Quota in MB for this mailbox. Leave empty to use the value defined at domain level."),
        widget=forms.widgets.TextInput(attrs={"class": "span1"})
    )
    aliases = forms.EmailField(
        label=ugettext_lazy("Alias(es)"),
        required=False,
        help_text=ugettext_lazy("Alias(es) of this mailbox. Indicate only one address per input, press ENTER to add a new input. Use the '*' character to create a 'catchall' alias (ex: *@domain.tld).")
    )

    def __init__(self, *args, **kwargs):
        if "instance" in kwargs:
            self.mb = kwargs["instance"]
            del kwargs["instance"]
        super(AccountFormMail, self).__init__(*args, **kwargs)
        if hasattr(self, "mb") and self.mb is not None:
            self.fields["email"].required = True
            cpt = 1
            for alias in self.mb.alias_set.all():
                if len(alias.get_recipients()) >= 2:
                    continue
                name = "aliases_%d" % cpt
                self._create_field(forms.EmailField, name, alias.full_address)
                cpt += 1
            self.fields["email"].initial = self.mb.full_address
            self.fields["quota"].initial = self.mb.quota

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "aliases", forms.EmailField)

    def clean_email(self):
        """Ensure lower case emails"""
        return self.cleaned_data["email"].lower()

    def save(self, user, account):
        if self.cleaned_data["email"] == "":
            return None

        locpart, domname = split_mailbox(self.cleaned_data["email"])
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise AdminError(_("Domain does not exist"))

        if not user.can_access(domain):
            raise PermDeniedException

        if not hasattr(self, "mb") or self.mb is None:
            try:
                self.mb = Mailbox.objects.get(address=locpart, domain=domain)
            except Mailbox.DoesNotExist:
                events.raiseEvent("CanCreate", user, "mailboxes")
                self.mb = Mailbox()
                self.mb.save_from_user(locpart, domain, account,
                                       self.cleaned_data["quota"],
                                       owner=user)
                grant_access_to_object(user, self.mb, is_owner=True)
                events.raiseEvent("CreateMailbox", user, self.mb)
                if user.is_superuser and not self.mb.user.has_perm("admin.add_domain"):
                    # A super user is creating a new mailbox. Give
                    # access to that mailbox (and the associated
                    # account) to the appropriate domain admins,
                    # except if the new account has a more important
                    # role (SuperAdmin, Reseller)
                    for admin in self.mb.domain.admins:
                        grant_access_to_object(admin, self.mb)
                        grant_access_to_object(admin, self.mb.user)

        else:
            old_mail_home = None
            if self.cleaned_data["email"] != self.mb.full_address:
                old_mail_home = self.mb.mail_home
                q = Quota.objects.get(username=self.mb.full_address)
                self.mb.domain = domain
                self.mb.address = locpart
                q.username = self.mb.full_address
                q.save()
            self.mb.set_quota(self.cleaned_data["quota"], user.has_perm("admin.add_domain"))
            self.mb.save()
            if old_mail_home is not None:
                # Problem here: the mailbox has already been saved so,
                # if the rename fails, we can't rollback!
                # Maybe django-reversion could be the solution?
                try:
                    self.mb.rename_dir(old_mail_home)
                except AdminError:
                    # do rollback
                    pass

        account.email = self.cleaned_data["email"]
        account.save()

        for name, value in self.cleaned_data.iteritems():
            if not name.startswith("aliases"):
                continue
            if value == "":
                continue
            local_part, domname = split_mailbox(value)
            try:
                self.mb.alias_set.get(address=local_part, domain__name=domname)
            except Alias.DoesNotExist:
                pass
            else:
                continue
            events.raiseEvent("CanCreate", user, "mailbox_aliases")
            al = Alias(address=local_part, enabled=account.is_active)
            al.domain = Domain.objects.get(name=domname)
            al.save([self.mb], [])
            grant_access_to_object(user, al, is_owner=True)
            events.raiseEvent("MailboxAliasCreated", user, al)
            if user.is_superuser:
                for admin in al.domain.admins:
                    grant_access_to_object(admin, al)

        for alias in self.mb.alias_set.all():
            if len(alias.get_recipients()) >= 2:
                continue
            if not len(filter(lambda name: self.cleaned_data[name] == alias.full_address,
                              self.cleaned_data.keys())):
                events.raiseEvent("MailboxAliasDeleted", alias)
                ungrant_access_to_object(alias)
                alias.delete()

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
        for pos, domain in enumerate(self.account.get_domains()):
            name = "domains_%d" % (pos + 1)
            self._create_field(DomainNameField, name, domain.name)
        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "domains", DomainNameField)

    def save(self):
        current_domains = map(lambda dom: dom.name, self.account.get_domains())
        for name, value in self.cleaned_data.iteritems():
            if not name.startswith("domains"):
                continue
            if value in ["", None]:
                continue
            if not value in current_domains:
                domain = Domain.objects.get(name=value)
                grant_access_to_object(self.account, domain)
                for mb in domain.mailbox_set.all():
                    if mb.user.has_perm("admin.add_domain"):
                        continue
                    grant_access_to_object(self.account, mb)
                    grant_access_to_object(self.account, mb.user)
                for al in Alias.objects.filter(domain=domain):
                    grant_access_to_object(self.account, al)

        for domain in self.account.get_domains():
            if not len(filter(lambda name: self.cleaned_data[name] == domain.name,
                              self.cleaned_data.keys())):
                ungrant_access_to_object(domain, self.account)
                for mb in domain.mailbox_set.all():
                    if mb.user.has_perm("admin.add_domain"):
                        continue
                    ungrant_access_to_object(mb, self.account)
                    ungrant_access_to_object(mb.user, self.account)
                for al in Alias.objects.filter(domain=domain):
                    ungrant_access_to_object(al, self.account)


class AccountForm(TabForms):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.forms = [
            dict(id="general", title=_("General"), cls=AccountFormGeneral,
                 new_args=[user], mandatory=True),
            dict(id="mail", title=_("Mail"), formtpl="admin/mailform.html",
                 cls=AccountFormMail),
            dict(id="perms", title=_("Permissions"), formtpl="admin/permsform.html",
                 cls=AccountPermissionsForm)
        ]
        cbargs = [user]
        if "instances" in kwargs:
            cbargs += [kwargs["instances"]["general"]]
        self.forms += events.raiseQueryEvent("ExtraAccountForm", *cbargs)

        super(AccountForm, self).__init__(*args, **kwargs)

    def check_perms(self, account):
        if account.is_superuser:
            return False
        return self.user.has_perm("admin.add_domain") \
            and account.has_perm("auth.add_user")

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

    def save_general_form(self):
        self.account = self.forms[0]["instance"].save()

    def save(self):
        """Custom save method

        As forms interact with each other, it is simpler to make
        custom code to save them.
        """
        self.forms[1]["instance"].save(self.user, self.account)
        if len(self.forms) <= 2:
            return
        for f in self.forms[2:]:
            f["instance"].save()

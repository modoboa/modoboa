# coding: utf-8
from django import forms
from django.contrib.auth.models import Group
from modoboa.admin.models import *
from django.utils.translation import ugettext as _, ugettext_noop
from django.http import QueryDict
from modoboa.admin.templatetags.admin_extras import gender
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.permissions import get_account_roles
from modoboa.lib.formutils import *
from modoboa.lib.permissions import *

class DomainForm(forms.ModelForm, DynamicForm):
    aliases = DomainNameField(
        label=ugettext_noop("Alias(es)"), 
        required=False,
        help_text=ugettext_noop("Alias(es) of this domain")
        )

    class Meta:
        model = Domain
        fields = ("name", "quota", "aliases", "enabled")

    def __init__(self, *args, **kwargs):
        self.oldname = None
        if kwargs.has_key("instance"):
            self.oldname = kwargs["instance"].name
        super(DomainForm, self).__init__(*args, **kwargs)

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "aliases", DomainNameField)
        elif kwargs.has_key("instance"):
            d = kwargs["instance"]
            for pos, dalias in enumerate(d.domainalias_set.all()):
                name = "aliases_%d" % (pos + 1)
                self._create_field(forms.CharField, name, dalias.name, 3)

    def clean(self):
        super(DomainForm, self).clean()
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
        d = super(DomainForm, self).save(commit=False)
        if commit:
            if self.oldname is not None and d.name != self.oldname:
                if not d.rename_dir(self.oldname):
                    raise AdminError(_("Failed to rename domain, check permissions"))
            d.save()
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
                    events.raiseEvent("DomainAliasDeleted", dalias)
                    ungrant_access_to_object(dalias)
                    dalias.delete()
        return d

class DlistForm(forms.ModelForm, DynamicForm):
    email = forms.EmailField(
        label=ugettext_noop("Email address"),
        help_text=ugettext_noop("")
        )
    recipients = forms.EmailField(
        label=ugettext_noop("Recipients"), required=False,
        help_text=ugettext_noop("Mailbox(es) this alias will point to")
        )

    class Meta:
        model = Alias
        fields = ("enabled",)

    def __init__(self, *args, **kwargs):
        super(DlistForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['email', 'recipients', 'enabled']

        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "recipients", forms.EmailField)
        elif kwargs.has_key("instance"):
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
            Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise forms.ValidationError(_("Domain does not exist"))
        return self.cleaned_data["email"]

    def set_recipients(self, user):
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
                if not user.can_access(domain):
                    raise PermDeniedException(v)
                try:
                    mb = Mailbox.objects.get(domain=domain, address=local_part)
                except Mailbox.DoesNotExist:
                    raise AdminError(_("Mailbox %s does not exist" % v))
                self.int_rcpts += [mb]
                total += 1
                continue

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

class ImportDataForm(forms.Form):
    sourcefile = forms.FileField(label=_("Select a file"))
    sepcar = forms.CharField(label=_("Separator"), max_length=1, required=False)

    def __init__(self, *args, **kwargs):
        super(ImportDataForm, self).__init__(*args, **kwargs)
        self.fields["sepcar"].widget.attrs = {"class" : "span1"}

    def clean_sepcar(self):
        if self.cleaned_data["sepcar"] == "":
            return ";"
        return str(self.cleaned_data["sepcar"])

class AccountFormGeneral(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[('', ugettext_noop("Choose"))]
        )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "role", "is_active")

    def __init__(self, user, *args, **kwargs):
        super(AccountFormGeneral, self).__init__(*args, **kwargs)
        
        self.fields["is_active"].label = _("Enabled")
        self.user = user
        if user.group == "DomainAdmins":
            del self.fields["role"]
            return

        self.fields["role"].choices = \
            [('', ugettext_noop("Choose"))] + get_account_roles(user)
        if kwargs.has_key("instance"):
            u = kwargs["instance"]
            if u.is_superuser:
                role = "SuperAdmins"
            else:
                try:
                    role = u.groups.all()[0].name
                except IndexError:
                    pass
            self.fields["role"].initial = role

    def save(self, commit=True):
        account = super(AccountFormGeneral, self).save(commit=False)
        if commit:
            account.save()
            role = None
            if self.cleaned_data.has_key("role"):
                role = self.cleaned_data["role"]
            elif self.user.group == "DomainAdmins" and self.user != account:
                role = "SimpleUsers"
            if role is not None:
                account.groups.clear()
                if role == "SuperAdmins":
                    account.is_superuser = True
                else:
                    account.is_superuser = False
                    account.groups.add(Group.objects.get(name=role))
                account.save()
        return account

class AccountFormGeneralPwd(AccountFormGeneral):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=ugettext_noop("Confirmation"), 
        widget=forms.PasswordInput,
        help_text=ugettext_noop("Enter the same password as above, for verification.")
        )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name",
                  "password1", "password2", "role", "is_active")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True, **kwargs):
        user = super(AccountFormGeneralPwd, self).save(**kwargs)
        if self.cleaned_data.has_key("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class AccountFormMail(forms.Form, DynamicForm):
    # FIXME
    # * Renommage de boite ?

    email = forms.EmailField(label=_("E-mail"), required=False)
    quota = forms.IntegerField(label=_("Quota"), required=False)
    aliases = forms.EmailField(
        label=ugettext_noop("Alias(es)"), 
        required=False,
        help_text=ugettext_noop("Alias(es) of this mailbox")
        )

    def __init__(self, *args, **kwargs):
        if kwargs.has_key("instance"):
            self.mb = kwargs["instance"]
            del kwargs["instance"]
        super(AccountFormMail, self).__init__(*args, **kwargs)
        if not hasattr(self, "mb") or self.mb is None:
            return
        self.fields["email"].required = True
        for pos, alias in enumerate(self.mb.alias_set.all()):
            if len(alias.get_recipients()) >= 2:
                continue
            name = "aliases_%d" % (pos + 1)
            self._create_field(forms.EmailField, name, alias.full_address)
        self.fields["email"].initial = self.mb.full_address
        self.fields["quota"].initial = self.mb.quota
        if len(args) and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "aliases", forms.EmailField)

    def save(self, user, account):
        if self.cleaned_data["email"] == "":
            return None

        locpart, domname = split_mailbox(self.cleaned_data["email"])
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise AdminError(_("Domain does not exist"))

        if not user.can_access(domain):
            raise PermDeniedException(_("You don't have access to this domain"))

        if not hasattr(self, "mb") or self.mb is None:
            try:
                self.mb = Mailbox.objects.get(address=locpart, domain=domain)
            except Mailbox.DoesNotExist:
                events.raiseEvent("CanCreate", user, "mailboxes")
                self.mb = Mailbox()
                self.mb.save_from_user(locpart, domain, account, 
                                       self.cleaned_data["quota"])
                grant_access_to_object(user, self.mb, is_owner=True)
                events.raiseEvent("CreateMailbox", user, self.mb)
        else:
            if self.cleaned_data["email"] != self.mb.full_address:
                if self.mb.rename_dir(domname, locpart):
                    self.mb.domain = domain
                    self.mb.address = locpart
                else:
                    raise AdminError(_("Failed to rename mailbox, check permissions"))
            self.mb.save(quota=self.cleaned_data["quota"])

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
        label=ugettext_noop("Domain(s)"), 
        required=False,
        help_text=ugettext_noop("Domain(s) that user administrates")
        )

    def __init__(self, *args, **kwargs):
        if kwargs.has_key("instance"):
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

        for domain in self.account.get_domains():
            if not len(filter(lambda name: self.cleaned_data[name] == domain.name, 
                              self.cleaned_data.keys())):
                ungrant_access_to_object(domain, self.account)

class AccountForm(TabForms):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.forms = [
            dict(id="general", title=_("General"), cls=AccountFormGeneralPwd,
                 new_args=[user], mandatory=True),
            dict(id="mail", title=_("Mail"), formtpl="admin/mailform.html",
                 cls=AccountFormMail),
            dict(id="perms", title=_("Permissions"), formtpl="admin/permsform.html",
                 cls=AccountPermissionsForm)
            ]
        cbargs = [user]
        if kwargs.has_key("instances"):
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


import reversion
from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib import events
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.exceptions import PermDeniedException
from modoboa.extensions.admin.exceptions import AdminError
from .base import DatesAware
from .domain import Domain
from .mailbox import Mailbox


class Alias(DatesAware):
    address = models.CharField(
        ugettext_lazy('address'), max_length=254,
        help_text=ugettext_lazy("The alias address (without the domain part). For a 'catch-all' address, just enter an * character.")
    )
    domain = models.ForeignKey(Domain)
    mboxes = models.ManyToManyField(
        Mailbox, verbose_name=ugettext_lazy('mailboxes'),
        help_text=ugettext_lazy("The mailboxes this alias points to")
    )
    aliases = models.ManyToManyField(
        'Alias',
        help_text=ugettext_lazy("The aliases this alias points to")
    )
    extmboxes = models.TextField(blank=True)
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy("Check to activate this alias")
    )

    class Meta:
        permissions = (
            ("view_aliases", "View aliases"),
        )
        unique_together = (("address", "domain"),)
        ordering = ["domain__name", "address"]
        app_label = 'admin'

    def __unicode__(self):
        return self.full_address

    @property
    def full_address(self):
        return "%s@%s" % (self.address, self.domain.name)

    @property
    def identity(self):
        return self.full_address

    @property
    def name_or_rcpt(self):
        rcpts_count = self.get_recipients_count()
        if not rcpts_count:
            return "---"
        rcpts = self.get_recipients()
        if rcpts_count > 1:
            return "%s, ..." % rcpts[0]
        return rcpts[0]

    @property
    def type(self):
        cpt = self.get_recipients_count()
        if cpt > 1:
            return "dlist"
        if self.extmboxes != "":
            return "forward"
        return "alias"

    @property
    def tags(self):
        labels = {
            "dlist": _("distribution list"),
            "forward": _("forward"),
            "alias": _("alias")
        }
        altype = self.type
        return [{"name": altype, "label": labels[altype], "type": "idt"}]

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(creator, self, is_owner=True)
        events.raiseEvent("MailboxAliasCreated", creator, self)
        if creator.is_superuser:
            for admin in self.domain.admins:
                grant_access_to_object(admin, self)

    def save(self, int_rcpts, ext_rcpts, *args, **kwargs):
        if len(ext_rcpts):
            self.extmboxes = ",".join(ext_rcpts)
        else:
            self.extmboxes = ""
        if "creator" in kwargs:
            creator = kwargs["creator"]
            del kwargs["creator"]
        else:
            creator = None
        super(Alias, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)
        curaliases = self.aliases.all()
        curmboxes = self.mboxes.all()
        for t in int_rcpts:
            if isinstance(t, Alias):
                if not t in curaliases:
                    self.aliases.add(t)
                continue
            if not t in curmboxes:
                self.mboxes.add(t)
        for t in curaliases:
            if not t in int_rcpts:
                self.aliases.remove(t)
        for t in curmboxes:
            if not t in int_rcpts:
                self.mboxes.remove(t)

    def delete(self):
        from modoboa.lib.permissions import ungrant_access_to_object

        events.raiseEvent("MailboxAliasDeleted", self)
        ungrant_access_to_object(self)
        super(Alias, self).delete()

    def get_recipients(self):
        """Return the recipients list

        Internal and external addresses are mixed into a single list.
        """
        result = [al.full_address for al in self.aliases.all()]
        result += [mb.full_address for mb in self.mboxes.all()]
        if self.extmboxes != "":
            result += self.extmboxes.split(',')
        return result

    def get_recipients_count(self):
        total = 0
        if self.extmboxes != "":
            total += len(self.extmboxes.split(','))
        return total + self.aliases.count() + self.mboxes.count()

    def ui_disabled(self, user):
        if user.is_superuser:
            return False
        for mb in self.mboxes.all():
            if not user.is_owner(mb.domain):
                return True
        return False

    def from_csv(self, user, row, expected_elements=5):
        """Create a new alias from a CSV file entry

        """
        if len(row) < expected_elements:
            raise AdminError(_("Invalid line: %s" % row))
        localpart, domname = split_mailbox(row[1].strip())
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise AdminError(_("Domain '%s' does not exist" % domname))
        if not user.can_access(domain):
            raise PermDeniedException
        self.address = localpart
        self.domain = domain
        self.enabled = (row[2].strip() == 'True')
        int_rcpts = []
        ext_rcpts = []
        for rcpt in row[3:]:
            rcpt = rcpt.strip()
            localpart, domname = split_mailbox(rcpt)
            try:
                Domain.objects.get(name=domname)
            except Domain.DoesNotExist:
                ext_rcpts += [rcpt]
                continue
            try:
                target = Alias.objects.get(domain__name=domname, address=localpart)
                if target.full_address == self.full_address:
                    target = None
            except Alias.DoesNotExist:
                target = None
            if target is None:
                try:
                    target = Mailbox.objects.get(address=localpart, 
                                                 domain__name=domname)
                except Mailbox.DoesNotExist:
                    raise AdminError(_("Local recipient %s not found" % rcpt))
            int_rcpts += [target]
        self.save(int_rcpts, ext_rcpts, creator=user)

    def to_csv(self, csvwriter):
        row = [self.type, self.full_address, self.enabled]
        row += self.get_recipients()
        csvwriter.writerow(row)

reversion.register(Alias)

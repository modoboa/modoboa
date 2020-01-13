"""Models related to aliases management."""

import hashlib
import random

from reversion import revisions as reversion

from django.db import models
from django.urls import reverse
from django.utils.encoding import (
    force_bytes, force_str, python_2_unicode_compatible, smart_text
)
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.core import signals as core_signals
from modoboa.lib.email_utils import split_mailbox
from modoboa.lib.exceptions import (
    BadRequest, Conflict, NotFound, PermDeniedException
)
from .. import signals
from .base import AdminObject
from .domain import Domain
from .mailbox import Mailbox


@python_2_unicode_compatible
class Alias(AdminObject):

    """Mailbox alias."""

    address = models.CharField(
        ugettext_lazy("address"), max_length=254,
        help_text=ugettext_lazy(
            "The alias address."
        )
    )
    domain = models.ForeignKey(Domain, null=True, on_delete=models.CASCADE)
    enabled = models.BooleanField(
        ugettext_lazy("enabled"),
        help_text=ugettext_lazy("Check to activate this alias"),
        default=True
    )
    internal = models.BooleanField(default=False)
    description = models.TextField(
        ugettext_lazy("Description"), blank=True)
    expire_at = models.DateTimeField(
        ugettext_lazy("Expire at"), blank=True, null=True)
    _objectname = "MailboxAlias"

    class Meta:
        ordering = ["address"]
        unique_together = (("address", "internal"), )
        app_label = "admin"

    def __str__(self):
        return smart_text(self.address)

    @classmethod
    def generate_random_address(cls):
        """Generate a random address (local part)."""
        m = hashlib.md5()
        for x in random.sample(range(10000000), 60):
            m.update(force_bytes(x))
        return m.hexdigest()[:20]

    @property
    def identity(self):
        return self.address

    @property
    def name_or_rcpt(self):
        rcpts_count = self.recipients_count
        if not rcpts_count:
            return "---"
        rcpts = self.recipients
        if rcpts_count > 1:
            return "%s, ..." % rcpts[0]
        return rcpts[0]

    @property
    def type(self):
        """FIXME: deprecated."""
        return "alias"

    @property
    def tags(self):
        return [{"name": "alias", "label": _("alias"), "type": "idt"}]

    def get_absolute_url(self):
        """Return detail url for this alias."""
        return reverse("admin:alias_detail", args=[self.pk])

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        super(Alias, self).post_create(creator)
        if creator.is_superuser:
            for admin in self.domain.admins:
                grant_access_to_object(admin, self)

    def set_recipients(self, address_list):
        """Set recipients for this alias.

        Special recipients:
        * local mailbox + extension: r_mailbox will be set to local mailbox
        * alias address == recipient address: valid only to keep local copies
          (when a forward is defined) and to create exceptions when a catchall
          is defined on the associated domain

        """
        for address in set(address_list):
            if not address:
                continue
            if self.aliasrecipient_set.filter(address=address).exists():
                continue
            local_part, domname, extension = (
                split_mailbox(address, return_extension=True))
            if domname is None:
                raise BadRequest(
                    u"%s %s" % (_("Invalid address"), address)
                )
            domain = Domain.objects.filter(name=domname).first()
            kwargs = {"address": address, "alias": self}
            if (
                (domain is not None) and
                (
                    any(
                        r[1] for r in signals.use_external_recipients.send(
                            self, recipients=address)
                    ) is False
                )
            ):
                rcpt = Mailbox.objects.filter(
                    domain=domain, address=local_part).first()
                if rcpt is None:
                    rcpt = Alias.objects.filter(
                        address="%s@%s" % (local_part, domname)
                    ).first()
                    if rcpt is None:
                        raise NotFound(
                            _("Local recipient {}@{} not found")
                            .format(local_part, domname)
                        )
                    if rcpt.address == self.address:
                        raise Conflict
                    kwargs["r_alias"] = rcpt
                else:
                    kwargs["r_mailbox"] = rcpt
            AliasRecipient(**kwargs).save()

        # Remove old recipients
        self.aliasrecipient_set.exclude(
            address__in=address_list).delete()

    @property
    def recipients(self):
        """Return the recipient list."""
        return (
            self.aliasrecipient_set.order_by("address")
            .values_list("address", flat=True)
        )

    @property
    def recipients_count(self):
        """Return the number of recipients of this alias."""
        return self.aliasrecipient_set.count()

    def from_csv(self, user, row, expected_elements=5):
        """Create a new alias from a CSV file entry."""
        if len(row) < expected_elements:
            raise BadRequest(_("Invalid line: %s" % row))
        address = row[1].strip().lower()
        localpart, domname = split_mailbox(address)
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise BadRequest(_("Domain '%s' does not exist" % domname))
        if not user.can_access(domain):
            raise PermDeniedException
        core_signals.can_create_object.send(
            sender="import", context=user, klass=Alias)
        core_signals.can_create_object.send(
            sender="import", context=domain, object_type="mailbox_aliases")
        if Alias.objects.filter(address=address, internal=False).exists():
            raise Conflict
        self.address = address
        self.domain = domain
        self.enabled = (row[2].strip().lower() in ["true", "1", "yes", "y"])
        self.save()
        self.set_recipients([raddress.strip() for raddress in row[3:]])
        self.post_create(user)

    def to_csv(self, csvwriter):
        row = ["alias", force_str(self.address), self.enabled]
        row += self.recipients
        csvwriter.writerow(row)


reversion.register(Alias)


@python_2_unicode_compatible
class AliasRecipient(models.Model):

    """An alias recipient."""

    address = models.EmailField()
    alias = models.ForeignKey(Alias, on_delete=models.CASCADE)

    # if recipient is a local mailbox
    r_mailbox = models.ForeignKey(Mailbox, blank=True, null=True,
                                  on_delete=models.CASCADE)
    # if recipient is a local alias
    r_alias = models.ForeignKey(
        Alias, related_name="alias_recipient_aliases", blank=True, null=True,
        on_delete=models.CASCADE)

    class Meta:
        app_label = "admin"
        db_table = "modoboa_admin_aliasrecipient"
        unique_together = [
            ("alias", "r_mailbox"),
            ("alias", "r_alias")
        ]

    def __str__(self):
        """Return alias and recipient."""
        return smart_text(
            "{} -> {}".format(self.alias.address, self.address)
        )

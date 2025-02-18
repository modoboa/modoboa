"""Models related to aliases management."""

import hashlib
import random

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str, smart_str
from django.utils.translation import gettext as _, gettext_lazy

from reversion import revisions as reversion

from modoboa.core import signals as core_signals
from modoboa.lib.email_utils import split_mailbox
from modoboa.lib.exceptions import (
    BadRequest,
    Conflict,
    NotFound,
    ModoboaException,
    AliasExists,
)
from .. import signals
from .base import AdminObject
from .domain import Domain
from .mailbox import Mailbox


def validate_alias_address(
    address, creator, internal=False, instance=None, ignore_existing=False
):
    """Check if the given alias address can be created by creator."""
    local_part, domain = split_mailbox(address.lower())
    domain = Domain.objects.filter(name=domain).first()
    if domain is None:
        raise ValidationError(_("Domain not found."))
    if not creator.can_access(domain):
        raise ValidationError(_("Permission denied."))
    if not instance or instance.address != address:
        alias = Alias.objects.filter(address=address, internal=internal)
        condition = alias.exists() and not ignore_existing
        if condition:
            raise AliasExists(alias.first().pk)
    if instance is None:
        try:
            # Check creator limits
            core_signals.can_create_object.send(
                sender="validate_alias_address", context=creator, klass=Alias
            )
            # Check domain limits
            core_signals.can_create_object.send(
                sender="validate_alias_address",
                context=domain,
                object_type="mailbox_aliases",
            )
        except ModoboaException as inst:
            raise ValidationError(str(inst)) from None
    return local_part, domain


class AliasManager(models.Manager):
    """Custom manager for Alias."""

    def create(self, *args, **kwargs):
        """Custom create method."""
        creator = kwargs.pop("creator", None)
        recipients = kwargs.pop("recipients", None)
        alias = super().create(*args, **kwargs)
        if creator:
            alias.post_create(creator)
        if recipients:
            alias.set_recipients(recipients)
        return alias

    def modify_or_create(self, address, recipients, creator, domain):
        """Add recipient if the alias already exists or create it."""

        alias = self.get_queryset().filter(address=address, internal=False)
        if alias.exists():
            alias.first().add_recipients(recipients)
            return
        self.create(
            creator=creator, domain=domain, address=address, recipients=recipients
        )


class Alias(AdminObject):
    """Mailbox alias."""

    address = models.CharField(
        gettext_lazy("address"),
        max_length=254,
        help_text=gettext_lazy("The alias address."),
    )
    domain = models.ForeignKey(Domain, null=True, on_delete=models.CASCADE)
    enabled = models.BooleanField(
        gettext_lazy("enabled"),
        help_text=gettext_lazy("Check to activate this alias"),
        default=True,
    )
    internal = models.BooleanField(default=False)
    description = models.TextField(gettext_lazy("Description"), blank=True)
    expire_at = models.DateTimeField(gettext_lazy("Expire at"), blank=True, null=True)
    _objectname = "MailboxAlias"

    objects = AliasManager()

    class Meta:
        ordering = ["address"]
        unique_together = (("address", "internal"),)
        app_label = "admin"

    def __str__(self):
        return self.address

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
            return f"{rcpts[0]}, ..."
        return rcpts[0]

    @property
    def type(self):
        return "alias"

    @property
    def tags(self):
        return [{"name": "alias", "label": _("alias"), "type": "idt"}]

    def get_absolute_url(self):
        """Return detail url for this alias."""
        return reverse("admin:alias_detail", args=[self.pk])

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object

        super().post_create(creator)
        if creator.is_superuser:
            for admin in self.domain.admins:
                grant_access_to_object(admin, self)

    def add_recipients(self, address_list):
        """Add recipients for this alias.

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
            local_part, domname, extension = split_mailbox(
                address, return_extension=True
            )
            if domname is None:
                raise BadRequest("{} {}".format(_("Invalid address"), address))
            domain = Domain.objects.filter(name=domname).first()
            kwargs = {"address": address, "alias": self}
            if (domain is not None) and (
                any(
                    r[1]
                    for r in signals.use_external_recipients.send(
                        self, recipients=address
                    )
                )
                is False
            ):
                rcpt = Mailbox.objects.filter(domain=domain, address=local_part).first()
                if rcpt is None:
                    rcpt = Alias.objects.filter(
                        address=f"{local_part}@{domname}"
                    ).first()
                    if rcpt is None:
                        raise NotFound(
                            _("Local recipient {}@{} not found").format(
                                local_part, domname
                            )
                        )
                    if rcpt.address == self.address:
                        raise Conflict
                    kwargs["r_alias"] = rcpt
                else:
                    kwargs["r_mailbox"] = rcpt
            AliasRecipient(**kwargs).save()

    def remove_recipient_or_delete(self, recipient_to_delete: str):
        """
        Delete the selected recipient from this alias
        or delete the whole alias if only one is left.
        """
        alias_recipients = list(self.recipients)
        if recipient_to_delete in alias_recipients:
            if len(alias_recipients) == 1:
                # Only recipient, we delete the Alias
                self.delete()
            else:
                alias_recipients.remove(recipient_to_delete)
                self.set_recipients(alias_recipients)
                self.save()

    def set_recipients(self, address_list):
        """Set recipients for this alias."""

        self.add_recipients(address_list)

        # Remove old recipients
        self.aliasrecipient_set.exclude(address__in=address_list).delete()

    @property
    def recipients(self):
        """Return the recipient list."""
        return self.aliasrecipient_set.order_by("address").values_list(
            "address", flat=True
        )

    @property
    def recipients_count(self):
        """Return the number of recipients of this alias."""
        return self.aliasrecipient_set.count()

    def from_csv(self, user, row, expected_elements=5, formopts=False, **kwargs):
        """Create a new alias from a CSV file entry."""
        if len(row) < expected_elements:
            raise BadRequest(_("Invalid line: {}").format(row))
        self.address = row[1].strip().lower()
        try:
            local_part, self.domain = validate_alias_address(self.address, user)
        except AliasExists as e:
            # If continue_if_exists is true, we simply update the alias
            # Else we throw the conflict issue
            continue_if_exists = False
            if formopts:
                continue_if_exists = formopts.get("continue_if_exists", False)
            if continue_if_exists:
                alias = Alias.objects.filter(
                    address=self.address, internal=False
                ).first()
                alias.add_recipients([raddress.strip() for raddress in row[3:]])
                alias.save()
                return
            else:
                raise e

        self.enabled = row[2].strip().lower() in ["true", "1", "yes", "y"]
        self.save()
        self.set_recipients([raddress.strip() for raddress in row[3:]])
        self.post_create(user)

    def to_csv_row(self):
        """Return a row to include in a CSV file."""
        row = ["alias", force_str(self.address), self.enabled]
        row += self.recipients
        return row

    def to_csv(self, csvwriter):
        csvwriter.writerow(self.to_csv_row())


reversion.register(Alias)


class AliasRecipient(models.Model):
    """An alias recipient."""

    address = models.EmailField()
    alias = models.ForeignKey(Alias, on_delete=models.CASCADE)

    # if recipient is a local mailbox
    r_mailbox = models.ForeignKey(
        Mailbox, blank=True, null=True, on_delete=models.CASCADE
    )
    # if recipient is a local alias
    r_alias = models.ForeignKey(
        Alias,
        related_name="alias_recipient_aliases",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        app_label = "admin"
        db_table = "modoboa_admin_aliasrecipient"
        unique_together = [("alias", "r_mailbox"), ("alias", "r_alias")]

    def __str__(self):
        """Return alias and recipient."""
        return smart_str(f"{self.alias.address} -> {self.address}")

"""
IMAP migration models.
"""

from django.db import models

from modoboa.admin.models import Mailbox
from modoboa.lib.cryptutils import encrypt, decrypt


class EmailProvider(models.Model):
    """Email provider model."""

    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    port = models.PositiveIntegerField(default=143)
    secured = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]


class EmailProviderDomain(models.Model):
    """Email provider domain class."""

    provider = models.ForeignKey(
        EmailProvider, on_delete=models.CASCADE, related_name="domains"
    )
    name = models.CharField(max_length=100, unique=True)
    new_domain = models.ForeignKey(
        "admin.Domain", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["provider", "name"]


class Migration(models.Model):
    """Represent mailboxes to migrate."""

    provider = models.ForeignKey(EmailProvider, on_delete=models.CASCADE)
    mailbox = models.ForeignKey(Mailbox, on_delete=models.CASCADE)
    username = models.CharField(max_length=254, unique=True)
    _password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    @property
    def password(self):
        """Password getter."""
        return decrypt(self._password)

    @password.setter
    def password(self, value):
        """Password setter."""
        self._password = encrypt(value)

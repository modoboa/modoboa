"""IMAP authentication backend for Django."""

import imaplib
import ssl

from django.utils.encoding import smart_bytes, smart_str
from django.utils.translation import gettext as _

from modoboa.core import models as core_models
from modoboa.lib import email_utils
from modoboa.lib.exceptions import ModoboaException
from modoboa.parameters import tools as param_tools

from . import models


class IMAPBackend:
    """IMAP authentication backend."""

    def authenticate(self, request, username=None, password=None):
        """Check the username/password and return a User."""
        if not param_tools.get_global_parameter("enabled_imapmigration"):
            return None
        condition = not param_tools.get_global_parameter(
            "auto_create_domain_and_mailbox", "admin"
        )
        if condition:
            # Automatic domain/mailbox is disabled. Deny auth to
            # prevent further issues...
            return None
        self.address, domain = email_utils.split_mailbox(username)
        provider_domain = (
            models.EmailProviderDomain.objects.filter(name=domain)
            .select_related("provider")
            .first()
        )
        if not provider_domain:
            # Domain not allowed for migration: failure
            return None
        address = provider_domain.provider.address
        port = provider_domain.provider.port
        try:
            if provider_domain.provider.secured:
                conn = imaplib.IMAP4_SSL(address, port)
            else:
                conn = imaplib.IMAP4(address, port)
        except (OSError, imaplib.IMAP4.error, ssl.SSLError) as error:
            raise ModoboaException(
                _(f"Connection to IMAP server failed: {error}")
            ) from None

        try:
            typ, data = conn.login(smart_bytes(username), smart_str(password))
        except imaplib.IMAP4.error:
            typ = "NO"
        conn.logout()
        if typ != "OK":
            return None
        self.provider_domain = provider_domain
        return self.get_or_create_user(username, password)

    def get_or_create_user(self, username, password):
        """Get a user or create it the first time.

        .. note::

           We assume the username is a valid email address.
        """
        orig_username = username
        # Check if old addresses must be converted
        if self.provider_domain.new_domain:
            username = f"{self.address}@{self.provider_domain.new_domain.name}"
        user, created = core_models.User.objects.get_or_create(
            username__iexact=username,
            defaults={"username": username.lower(), "email": username.lower()},
        )
        if created:
            user.set_password(password)
            user.save()
            core_models.populate_callback(user)
            models.Migration.objects.create(
                provider=self.provider_domain.provider,
                mailbox=user.mailbox,
                username=orig_username,
                password=password,
            )
        else:
            # What happens if an account already exists?
            if not hasattr(user, "mailbox"):
                # No mailbox => might be an admin account
                return None
            qset = models.Migration.objects.filter(mailbox=user.mailbox)
            if not qset.exists():
                # No migration => either someone else account, or
                # migration is done
                return None
            if not user.check_password(password):
                # User may have changed its password on modoboa
                # Remote password and local now differs
                # We block the connection in that case
                return None
        return user

    def get_user(self, user_pk):
        """Retrieve a User instance."""
        user = None
        try:
            user = core_models.User.objects.get(pk=user_pk)
        except core_models.User.DoesNotExist:
            pass
        return user

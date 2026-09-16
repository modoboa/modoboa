"""Tests for the sender re-check made when a scheduled message leaves."""

from django.core import mail
from django.utils import timezone

from modoboa.admin import factories as admin_factories
from modoboa.webmail import constants, factories, jobs
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

SENDING = constants.SchedulingState.SENDING.value
SEND_ERROR = constants.SchedulingState.SEND_ERROR.value


class ScheduledSenderTestCase(WebmailTestCase):
    """Rights are checked again when the message is about to be sent.

    The relay used for scheduled sendings does not authenticate, so this
    is the only thing standing between a revoked address and a sent
    message.
    """

    def setUp(self):
        super().setUp()
        mail.outbox = []

    def _message(self, sender=None, **kwargs):
        kwargs.setdefault("scheduled_datetime", timezone.now())
        return factories.ScheduledMessageFactory(
            account=self.user,
            sender=sender or self.user.email,
            status=SENDING,
            **kwargs,
        )

    def _assert_refused(self, message, error):
        message.refresh_from_db()
        self.assertEqual(message.status, SEND_ERROR)
        self.assertEqual(message.error, error)
        self.assertEqual(len(mail.outbox), 0)

    def test_message_is_sent_when_nothing_changed(self):
        message = self._message()
        jobs.send_scheduled_message(message.id)
        self.assertEqual(len(mail.outbox), 1)

    def test_disabled_account(self):
        message = self._message()
        self.user.is_active = False
        self.user.save()
        jobs.send_scheduled_message(message.id)
        self._assert_refused(message, "The account has been disabled")

    def test_disabled_domain(self):
        message = self._message()
        domain = self.user.mailbox.domain
        domain.enabled = False
        domain.save()
        jobs.send_scheduled_message(message.id)
        self._assert_refused(message, "The domain has been disabled")

    def test_deleted_mailbox(self):
        message = self._message()
        self.user.mailbox.delete()
        jobs.send_scheduled_message(message.id)
        self._assert_refused(message, "The mailbox no longer exists")

    def test_address_no_longer_allowed(self):
        """An address granted to the mailbox is revoked after scheduling."""
        address = admin_factories.SenderAddressFactory(
            address="shared@example.test", mailbox=self.user.mailbox
        )
        message = self._message(sender=address.address)
        address.delete()
        jobs.send_scheduled_message(message.id)
        self._assert_refused(
            message, "This address is no longer allowed for this account"
        )

    def test_granted_address_is_still_allowed(self):
        address = admin_factories.SenderAddressFactory(
            address="shared@example.test", mailbox=self.user.mailbox
        )
        message = self._message(sender=address.address)
        jobs.send_scheduled_message(message.id)
        self.assertEqual(len(mail.outbox), 1)

    def test_refused_message_is_kept(self):
        """The message stays, so that the user can fix it and reschedule."""
        message = self._message()
        self.user.is_active = False
        self.user.save()
        jobs.send_scheduled_message(message.id)
        self.assertTrue(
            type(message).objects.filter(pk=message.pk).exists(),
        )

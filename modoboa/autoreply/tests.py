"""Autoreply model tests."""

from unittest import mock

from sievelib.factory import FiltersSet

from modoboa.admin import factories as admin_factories
from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase

from . import models


class SieveRuleTestCase(ModoTestCase):
    """Tests for the generated Sieve autoreply rule."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        admin_factories.populate_database()
        cls.account = User.objects.get(username="user@test.com")

    def _build_rule(self, subject, content):
        armessage = models.ARmessage.objects.create(
            mbox=self.account.mailbox,
            subject=subject,
            content=content,
            enabled=True,
        )
        request = mock.Mock()
        request.localconfig.parameters.get_value.return_value = 1
        fset = FiltersSet("test")
        armessage.update_sieve_rule(request, fset)
        return str(fset)

    def test_subject_and_content_are_escaped(self):
        """A break-out payload must not inject Sieve commands."""
        sieve = self._build_rule(
            subject='off"; redirect "attacker@evil.test',
            content='body"; discard; #',
        )
        # The injected quotes must be escaped, so the break-out sequences
        # never appear unescaped in the generated script.
        self.assertNotIn('redirect "attacker', sieve)
        self.assertNotIn('body"; discard', sieve)
        self.assertIn('\\"', sieve)

    def test_legitimate_content_preserved(self):
        sieve = self._build_rule(subject="Absent", content="Back soon")
        self.assertIn("Absent", sieve)
        self.assertIn("Back soon", sieve)

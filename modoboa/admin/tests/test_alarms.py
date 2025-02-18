"""Alarm related tests."""

from modoboa.lib.tests import ModoTestCase
from ..factories import populate_database
from ..models import Alarm, Domain


class AlarmsTestCase(ModoTestCase):
    """Alarm open/close test cases."""

    def setUp(self):
        super().setUp()
        populate_database()

    def test_set_forward(self):
        domain = Domain.objects.all().first()
        alarm = Alarm.objects.create(domain=domain, mailbox=None, title="Test alarm 3")
        alarm.save()
        self.assertEqual(alarm.status, 1)
        alarm.close()
        self.assertEqual(alarm.status, 2)
        alarm.reopen()
        self.assertEqual(alarm.status, 1)

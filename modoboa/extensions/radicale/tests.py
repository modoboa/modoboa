"""
Radicale extension unit tests.
"""
import os
import tempfile
from ConfigParser import SafeConfigParser

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core import management

from modoboa.lib import parameters
from modoboa.lib.tests import ExtTestCase
from modoboa.extensions.admin.factories import (
    MailboxFactory, populate_database
)
from modoboa.extensions.admin.models import (
    Domain, Mailbox
)

from .factories import (
    UserCalendarFactory, SharedCalendarFactory, AccessRuleFactory
)
from .models import UserCalendar, SharedCalendar, AccessRule


class UserCalendarTestCase(ExtTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(UserCalendarTestCase, self).setUp()
        self.activate_extensions('radicale')
        populate_database()

    def assertRuleEqual(self, calname, username, read=False, write=False):
        acr = AccessRule.objects.get(
            mailbox__user__username=username,
            calendar__name=calname)
        self.assertEqual(acr.read, read)
        self.assertEqual(acr.write, write)

    def test_add_calendar(self):
        MailboxFactory(
            address="polo", domain__name="test.com",
            user__username="polo@test.com")

        # As a super administrator
        mbox = Mailbox.objects.get(address='user', domain__name='test.com')
        values = {
            "name": "Test calendar",
            "mailbox": mbox.pk,
            "username": "admin@test.com",
            "read_access": 1,
            "stepid": "step2"
        }
        self.ajax_post(
            reverse("radicale:user_calendar_add"), values)
        self.clt.logout()
        self.assertRuleEqual("Test calendar", "admin@test.com", read=True)

        # As a domain administrator
        self.clt.login(username="admin@test.com", password="toto")
        values = {
            "name": "Test calendar 2",
            "mailbox": mbox.pk,
            "username": "admin@test.com",
            "read_access": 1,
            "write_access": 1,
            "stepid": "step2"
        }
        self.ajax_post(
            reverse("radicale:user_calendar_add"), values)
        self.clt.logout()
        self.assertRuleEqual(
            "Test calendar 2", "admin@test.com", read=True, write=True
        )

        # As a user
        self.clt.login(username="user@test.com", password="toto")
        values = {
            "name": "My calendar",
            "username": "admin@test.com",
            "read_access": 1,
            "write_access": 1,
            "username_1": "polo@test.com",
            "write_access_1": 1,
            "stepid": "step2"
        }
        self.ajax_post(
            reverse("radicale:user_calendar_add"), values)
        UserCalendar.objects.get(name="My calendar")
        self.assertRuleEqual(
            "My calendar", "admin@test.com", read=True, write=True)
        self.assertRuleEqual("My calendar", "polo@test.com", write=True)

    def test_edit_calendar(self):
        cal = UserCalendarFactory(
            mailbox__user__username='test@modoboa.org',
            mailbox__address='test', mailbox__domain__name='modoboa.org')
        values = {
            "name": "Modified", "mailbox": cal.mailbox.pk
        }
        self.ajax_post(
            reverse("radicale:user_calendar", args=[cal.pk]), values
        )

    def test_del_calendar(self):
        cal = UserCalendarFactory(
            mailbox__user__username='test@modoboa.org',
            mailbox__address='test', mailbox__domain__name='modoboa.org')
        self.ajax_delete(
            reverse("radicale:user_calendar", args=[cal.pk])
        )
        with self.assertRaises(ObjectDoesNotExist):
            UserCalendar.objects.get(pk=cal.pk)

    def test_del_calendar_denied(self):
        cal = UserCalendarFactory(
            mailbox__user__username='test@modoboa.org',
            mailbox__address='test', mailbox__domain__name='modoboa.org')
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        self.ajax_delete(
            reverse("radicale:user_calendar", args=[cal.pk]), status=403
        )

    def test_add_calendar_denied(self):
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        values = {
            "name": "Test calendar",
            "mailbox": Mailbox.objects.get(
                address="user", domain__name="test2.com").pk,
            "stepid": "step2"
        }
        self.ajax_post(
            reverse("radicale:user_calendar_add"), values, status=400)


class SharedCalendarTestCase(ExtTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(SharedCalendarTestCase, self).setUp()
        self.activate_extensions('radicale')
        populate_database()

    def test_add_calendar(self):
        # As a super administrator
        domain = Domain.objects.get(name="test.com")
        values = {
            "name": "Test calendar",
            "domain": domain.pk,
        }
        self.ajax_post(
            reverse("radicale:shared_calendar_add"), values)
        self.clt.logout()

        # As a domain administrator
        self.clt.login(username="admin@test.com", password="toto")
        values = {
            "name": "Test calendar 2",
            "domain": domain.pk
        }
        self.ajax_post(
            reverse("radicale:shared_calendar_add"), values)
        self.clt.logout()

    def test_add_calendar_denied(self):
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        values = {
            "name": "Test calendar",
            "domain": Domain.objects.get(name="test2.com")
        }
        self.ajax_post(
            reverse("radicale:shared_calendar_add"), values, status=400)

    def test_edit_calendar(self):
        cal = SharedCalendarFactory(
            domain__name='modoboa.org')
        values = {
            "name": "Modified", "domain": cal.domain.pk
        }
        self.ajax_post(
            reverse("radicale:shared_calendar", args=[cal.pk]), values
        )
        cal = SharedCalendar.objects.get(pk=cal.pk)
        self.assertEqual(cal.name, "Modified")

    def test_del_calendar(self):
        cal = SharedCalendarFactory(domain__name='modoboa.org')
        self.ajax_delete(
            reverse("radicale:shared_calendar", args=[cal.pk])
        )
        with self.assertRaises(ObjectDoesNotExist):
            SharedCalendar.objects.get(pk=cal.pk)

    def test_del_calendar_denied(self):
        cal = SharedCalendarFactory(domain__name='modoboa.org')
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        self.ajax_delete(
            reverse("radicale:shared_calendar", args=[cal.pk]), status=403
        )


class AccessRuleTestCase(ExtTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(AccessRuleTestCase, self).setUp()
        self.activate_extensions('radicale')
        populate_database()
        self.rights_file_path = tempfile.mktemp()
        parameters.save_admin(
            "RIGHTS_FILE_PATH", self.rights_file_path, app="radicale")

    def tearDown(self):
        os.unlink(self.rights_file_path)

    def test_rights_file_generation(self):
        mbox = Mailbox.objects.get(address="admin", domain__name="test.com")
        cal = UserCalendarFactory(mailbox=mbox)

        AccessRuleFactory(
            mailbox=Mailbox.objects.get(
                address="user", domain__name="test.com"),
            calendar=cal, read=True)
        management.call_command("generate_rights", verbosity=False)

        cfg = SafeConfigParser()
        with open(self.rights_file_path) as fpo:
            cfg.readfp(fpo)

        # Check mandatory rules
        self.assertTrue(cfg.has_section("domain-shared-calendars"))
        self.assertTrue(cfg.has_section("owners-access"))

        # Check user-defined rules
        section = "user@test.com-to-User calendar 1-acr"
        self.assertTrue(cfg.has_section(section))
        self.assertEqual(cfg.get(section, "user"), "user@test.com")
        self.assertEqual(
            cfg.get(section, "collection"),
            "test.com/user/admin/User calendar 1"
        )
        self.assertEqual(cfg.get(section, "permission"), "r")

    def test_rights_file_generation_with_admin(self):
        parameters.save_admin(
            "ALLOW_CALENDARS_ADMINISTRATION", "yes", app="radicale")
        management.call_command("generate_rights", verbosity=False)
        cfg = SafeConfigParser()
        with open(self.rights_file_path) as fpo:
            cfg.readfp(fpo)

        # Check mandatory rules
        self.assertTrue(cfg.has_section("domain-shared-calendars"))
        self.assertTrue(cfg.has_section("owners-access"))

        # Super admin rules
        section = "sa-admin-acr"
        self.assertTrue(cfg.has_section(section))

        # Domain admin rules
        for section in ["da-admin@test.com-to-test.com-acr",
                        "da-admin@test2.com-to-test2.com-acr"]:
            self.assertTrue(cfg.has_section(section))

"""Radicale extension unit tests."""

import os
import tempfile
from unittest import mock

from caldav import Event

from configparser import ConfigParser

from django.urls import reverse
from django.core import management
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core import factories as core_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase

from modoboa.admin.factories import populate_database

from . import factories
from . import jobs
from . import models
from . import mocks


class TestDataMixin:
    """Create some data."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()
        cls.account = core_models.User.objects.get(username="user@test.com")
        cls.calendar = factories.UserCalendarFactory(mailbox=cls.account.mailbox)
        cls.admin_account = core_models.User.objects.get(username="admin@test.com")
        cls.calendar2 = factories.UserCalendarFactory(mailbox=cls.admin_account.mailbox)
        cls.acr1 = factories.AccessRuleFactory(
            calendar=cls.calendar,
            mailbox=cls.admin_account.mailbox,
            read=True,
            write=True,
        )
        cls.account2 = core_factories.UserFactory(
            username="user2@test.com",
            groups=("SimpleUsers",),
        )
        admin_factories.MailboxFactory.create(
            address="user2", domain=cls.account.mailbox.domain, user=cls.account2
        )
        cls.domain = admin_models.Domain.objects.get(name="test.com")
        cls.scalendar = factories.SharedCalendarFactory(domain=cls.domain)
        cls.domain2 = admin_models.Domain.objects.get(name="test2.com")
        cls.scalendar2 = factories.SharedCalendarFactory(domain=cls.domain2)


class AccessRuleTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()
        populate_database()

    def setUp(self):
        """Initialize tests."""
        super().setUp()
        self.rights_file_path = tempfile.mktemp()
        self.set_global_parameter(
            "rights_file_path", self.rights_file_path, app="calendars"
        )

    def tearDown(self):
        os.unlink(self.rights_file_path)

    def test_rights_file_generation(self):
        mbox = admin_models.Mailbox.objects.get(
            address="admin", domain__name="test.com"
        )
        cal = factories.UserCalendarFactory(mailbox=mbox)

        acr = factories.AccessRuleFactory(
            mailbox=admin_models.Mailbox.objects.get(
                address="user", domain__name="test.com"
            ),
            calendar=cal,
            read=True,
        )
        management.call_command("generate_rights", verbosity=False)

        cfg = ConfigParser()
        with open(self.rights_file_path) as fpo:
            cfg.read_file(fpo)

        # Check mandatory rules
        # self.assertTrue(cfg.has_section("domain-shared-calendars"))
        self.assertTrue(cfg.has_section("principal"))
        self.assertTrue(cfg.has_section("calendars"))

        # Check user-defined rules
        section = f"acr-{acr.pk}-user@test.com-to-{cal.path}"
        self.assertTrue(cfg.has_section(section))
        self.assertEqual(cfg.get(section, "user"), "user@test.com")
        self.assertEqual(cfg.get(section, "collection"), f"admin@test.com/{cal.name}")
        self.assertEqual(cfg.get(section, "permissions"), "Rr")

        # Call a second time
        jobs.generate_rights()

    def _read_rights_file(self):
        cfg = ConfigParser()
        with open(self.rights_file_path) as fpo:
            cfg.read_file(fpo)
        return cfg

    def test_rights_file_rule_deletion(self):
        """A deleted access rule must disappear from the rights file."""
        owner = admin_models.Mailbox.objects.get(
            address="admin", domain__name="test.com"
        )
        grantee = admin_models.Mailbox.objects.get(
            address="user", domain__name="test.com"
        )
        cal = factories.UserCalendarFactory(mailbox=owner)
        acr = factories.AccessRuleFactory(
            mailbox=grantee, calendar=cal, read=True, write=True
        )
        jobs.generate_rights()
        section = f"acr-{acr.pk}-{grantee}-to-{cal.path}"
        self.assertTrue(self._read_rights_file().has_section(section))

        acr.delete()
        jobs.generate_rights()
        self.assertFalse(self._read_rights_file().has_section(section))

    def test_rights_file_calendar_creation(self):
        """A new calendar gets its token rule without any access rule change."""
        jobs.generate_rights()
        mbox = admin_models.Mailbox.objects.get(
            address="admin", domain__name="test.com"
        )
        cal = factories.UserCalendarFactory(mailbox=mbox)
        jobs.generate_rights()
        self.assertTrue(
            self._read_rights_file().has_section(
                f"token-usercalendar-{cal.pk}-{cal.path}"
            )
        )

    def test_rights_file_sections_are_unique(self):
        """Radicale refuses to start if a section is duplicated."""
        grantee = admin_models.Mailbox.objects.get(
            address="user", domain__name="test.com"
        )
        paths = []
        # Two owners sharing a calendar with the same name
        for address, domain in [("admin", "test.com"), ("admin", "test2.com")]:
            owner = admin_models.Mailbox.objects.get(
                address=address, domain__name=domain
            )
            cal = factories.UserCalendarFactory(mailbox=owner, name="Work")
            factories.AccessRuleFactory(mailbox=grantee, calendar=cal, read=True)
            paths.append(cal.path)
        # Two calendars with the same path (possible with existing data)
        factories.UserCalendarFactory(mailbox=grantee, name="Duplicate")
        other = factories.UserCalendarFactory(mailbox=grantee, name="Other")
        models.UserCalendar.objects.filter(pk=other.pk).update(
            _path="user@test.com/Duplicate"
        )
        jobs.generate_rights()

        # ConfigParser is strict by default, like Radicale
        cfg = self._read_rights_file()
        collections = [
            cfg.get(section, "collection")
            for section in cfg.sections()
            if cfg.get(section, "user") == grantee.full_address
        ]
        self.assertEqual(sorted(collections), sorted(paths))
        tokens = [
            section
            for section in cfg.sections()
            if cfg.get(section, "collection") == "user@test.com/Duplicate"
        ]
        self.assertEqual(len(tokens), 2)

    def test_rights_file_not_rewritten_when_unchanged(self):
        """The file is left untouched when rules did not change."""
        jobs.generate_rights()
        with open(self.rights_file_path) as fpo:
            content = fpo.read()
        jobs.generate_rights()
        with open(self.rights_file_path) as fpo:
            self.assertEqual(fpo.read(), content)
        management.call_command("generate_rights", force=True)
        with open(self.rights_file_path) as fpo:
            self.assertNotEqual(fpo.read(), content)

    def test_rights_file_generation_with_admin(self):
        self.set_global_parameter(
            "allow_calendars_administration", True, app="calendars"
        )
        management.call_command("generate_rights", verbosity=False)
        cfg = ConfigParser()
        with open(self.rights_file_path) as fpo:
            cfg.read_file(fpo)

        # Check mandatory rules
        # self.assertTrue(cfg.has_section("domain-shared-calendars"))
        self.assertTrue(cfg.has_section("principal"))
        self.assertTrue(cfg.has_section("calendars"))

        # Super admin rules
        section = "sa-admin-acr"
        self.assertTrue(cfg.has_section(section))

        # Domain admin rules
        for section in [
            "da-admin@test.com-to-test.com-acr",
            "da-admin@test2.com-to-test2.com-acr",
        ]:
            self.assertTrue(cfg.has_section(section))


class UserCalendarViewSetTestCase(TestDataMixin, ModoAPITestCase):
    """UserCalendar viewset tests."""

    def setUp(self):
        """Initiate test context."""
        self.client.force_authenticate(self.account)
        self.set_global_parameter("server_location", "http://localhost:5232")

    def test_get_calendars(self):
        """List or retrieve calendars."""
        url = reverse("api:user-calendar-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        url = reverse("api:user-calendar-detail", args=[self.calendar.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @mock.patch("caldav.DAVClient")
    def test_create_calendar(self, client_mock):
        """Create a new calendar."""
        client_mock.return_value = mocks.DAVClientMock()
        data = {"username": "user@test.com", "password": "toto"}
        response = self.client.post(reverse("core:login"), data)

        data = {"name": "Test calendaré", "color": "#ffffff"}
        url = reverse("api:user-calendar-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    @mock.patch("caldav.DAVClient")
    def test_create_calendar_rejects_rights_injection(self, client_mock):
        """A newline in the name must not reach the rights file."""
        client_mock.return_value = mocks.DAVClientMock()
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

        url = reverse("api:user-calendar-list")
        payload = {
            "name": (
                "cal\n[zzz-pwned]\nuser: attacker@example\n"
                "collection: .*\npermissions: RrWw\n#"
            ),
            "color": "#ffffff",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        self.assertFalse(
            models.UserCalendar.objects.filter(name__contains="zzz-pwned").exists()
        )

    @mock.patch("caldav.DAVClient")
    def test_create_calendar_rejects_radicale_forbidden_characters(self, client_mock):
        """Radicale refuses paths containing some characters."""
        client_mock.return_value = mocks.DAVClientMock()
        url = reverse("api:user-calendar-list")
        payload = {"name": "Réunions d'équipe", "color": "#ffffff"}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())

    @mock.patch("caldav.DAVClient")
    def test_create_calendar_with_existing_name(self, client_mock):
        """Calendar names are unique per owner, ignoring case."""
        client_mock.return_value = mocks.DAVClientMock()
        url = reverse("api:user-calendar-list")
        for name in [self.calendar.name, self.calendar.name.upper()]:
            with self.subTest(name=name):
                response = self.client.post(
                    url, {"name": name, "color": "#ffffff"}, format="json"
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("name", response.json())
        # Other users can use the same name
        self.client.force_authenticate(self.admin_account)
        response = self.client.post(
            url, {"name": self.calendar.name, "color": "#ffffff"}, format="json"
        )
        self.assertEqual(response.status_code, 201)

    @mock.patch("caldav.DAVClient")
    @mock.patch("caldav.Calendar")
    def test_rename_calendar_with_existing_name(self, cal_mock, client_mock):
        client_mock.return_value = mocks.DAVClientMock()
        cal_mock.return_value = mocks.Calendar()
        other = factories.UserCalendarFactory(mailbox=self.account.mailbox)
        url = reverse("api:user-calendar-detail", args=[other.pk])
        response = self.client.put(
            url, {"name": self.calendar.name, "color": "#ffffff"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        # Keeping its own name is allowed
        response = self.client.put(
            url, {"name": other.name, "color": "#000000"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_new_calendar_does_not_reuse_path_of_renamed_one(self):
        """A renamed calendar keeps its path, a new one must not take it."""
        calendar = factories.UserCalendarFactory(
            mailbox=self.account.mailbox, name="Work"
        )
        calendar.name = "Job"
        calendar.save()
        new_calendar = factories.UserCalendarFactory(
            mailbox=self.account.mailbox, name="work"
        )
        self.assertEqual(calendar.path, "user@test.com/Work")
        self.assertEqual(new_calendar.path, "user@test.com/work-2")

    def test_calendar_name_validator(self):
        for name in ["Test calendaré", "Mon agenda (perso)", "v1.2", "A & B"]:
            with self.subTest(name=name):
                models.calendar_name_validator(name)
        invalid_names = [
            f"cal{char}endar" for char in models.CALENDAR_NAME_FORBIDDEN_CHARACTERS
        ] + [".", "..", "cal\nendar", "cal\tendar", "cal\x00", "cal\x7f", "cal\u200b"]
        for name in invalid_names:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    models.calendar_name_validator(name)

    @mock.patch("caldav.DAVClient")
    @mock.patch("caldav.Calendar")
    def test_update_calendar(self, cal_mock, client_mock):
        """Update existing calendar."""
        client_mock.return_value = mocks.DAVClientMock()
        cal_mock.return_value = mocks.Calendar()
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

        data = {"name": "Modified calendar", "color": "#ffffff"}
        url = reverse("api:user-calendar-detail", args=[self.calendar.pk])
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        oldpath = self.calendar.path
        self.calendar.refresh_from_db()
        self.assertEqual(self.calendar.name, data["name"])
        self.assertEqual(self.calendar.path, oldpath)

    def test_delete_calendar(self):
        """Delete existing calendar."""
        url = reverse("api:user-calendar-detail", args=[self.calendar.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(models.UserCalendar.DoesNotExist):
            self.calendar.refresh_from_db()

    def test_check_token(self):
        """Check token access."""
        url = reverse("api:user-calendar-check-token")
        data = {"calendar": self.calendar._path, "token": self.calendar.access_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

        data["token"] = "pouet"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ko")

        data["calendar"] = "unknown"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 404)


class SharedCalendarViewSetTestCase(TestDataMixin, ModoAPITestCase):
    """SharedCalendar viewset tests."""

    def setUp(self):
        """Initiate test context."""
        self.client.force_authenticate(self.admin_account)
        self.set_global_parameter("server_location", "http://localhost:5232")

    def test_get_calendars(self):
        """List or retrieve calendars."""
        url = reverse("api:shared-calendar-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        url = reverse("api:shared-calendar-detail", args=[self.scalendar.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        account = core_models.User.objects.get(username="user@test.com")
        self.client.force_login(account)
        url = reverse("api:shared-calendar-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    @mock.patch("caldav.DAVClient")
    def test_create_calendar(self, client_mock):
        """Create a new calendar."""
        client_mock.return_value = mocks.DAVClientMock()
        data = {"username": "admin@test.com", "password": "toto"}
        response = self.client.post(reverse("core:login"), data)

        data = {
            "name": "Shared calendar",
            "color": "#ffffff",
            "domain": {"pk": self.domain.pk, "name": "test.com"},
        }
        url = reverse("api:shared-calendar-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    @mock.patch("caldav.DAVClient")
    def test_create_calendar_with_existing_name(self, client_mock):
        """Calendar names are unique per domain."""
        client_mock.return_value = mocks.DAVClientMock()
        self.client.force_authenticate(self.sadmin)
        url = reverse("api:shared-calendar-list")
        data = {
            "name": self.scalendar.name,
            "color": "#ffffff",
            "domain": {"pk": self.domain.pk, "name": "test.com"},
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        # Another domain can use the same name
        data["domain"] = {"pk": self.domain2.pk, "name": "test2.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    @mock.patch("caldav.DAVClient")
    def test_create_calendar_rejects_unowned_domain(self, client_mock):
        """A shared calendar cannot be created under an unmanaged domain.

        admin@test.com only administers test.com, so it must not be able to
        create a shared calendar under test2.com.
        """
        client_mock.return_value = mocks.DAVClientMock()
        data = {"username": "admin@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

        data = {
            "name": "Evil shared calendar",
            "color": "#ffffff",
            "domain": {"pk": self.domain2.pk, "name": "test2.com"},
        }
        url = reverse("api:shared-calendar-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            models.SharedCalendar.objects.filter(name="Evil shared calendar").exists()
        )

    @mock.patch("caldav.DAVClient")
    @mock.patch("caldav.Calendar")
    def test_update_calendar(self, cal_mock, client_mock):
        """Update existing calendar."""
        client_mock.return_value = mocks.DAVClientMock()
        cal_mock.return_value = mocks.Calendar()
        data = {"username": "admin@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

        data = {
            "name": "Modified calendar",
            "color": "#ffffff",
            "domain": {"pk": self.domain.pk, "name": "test.com"},
        }
        url = reverse("api:shared-calendar-detail", args=[self.scalendar.pk])
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        oldpath = self.scalendar.path
        self.scalendar.refresh_from_db()
        self.assertEqual(self.scalendar.name, data["name"])
        self.assertEqual(self.scalendar.path, oldpath)

    def test_delete_calendar(self):
        """Delete existing calendar."""
        url = reverse("api:shared-calendar-detail", args=[self.scalendar.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(models.SharedCalendar.DoesNotExist):
            self.scalendar.refresh_from_db()

    def test_check_token(self):
        """Check token access."""
        url = reverse("api:shared-calendar-check-token")
        data = {"calendar": self.scalendar._path, "token": self.scalendar.access_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

        data["token"] = "pouet"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ko")

        data["calendar"] = "unknown"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 404)


class AccessRuleViewSetTestCase(TestDataMixin, ModoAPITestCase):
    """AccessRule viewset tests."""

    def setUp(self):
        """Initiate test context."""
        self.client.force_authenticate(self.account)

    def _rule_data(self, mailbox, **kwargs):
        data = {
            "mailbox": {"pk": mailbox.pk, "full_address": mailbox.full_address},
            "read": True,
        }
        data.update(kwargs)
        return data

    def test_get_accessrules(self):
        """Test access rule retrieval."""
        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["pk"], self.acr1.pk)

    def test_get_accessrules_scoped_to_calendar(self):
        """Rules of another calendar of the same user must not be listed."""
        other_calendar = factories.UserCalendarFactory(mailbox=self.account.mailbox)
        other_rule = factories.AccessRuleFactory(
            calendar=other_calendar, mailbox=self.admin_account.mailbox, read=True
        )
        url = reverse("api:access-rule-list", args=[other_calendar.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([rule["pk"] for rule in response.json()], [other_rule.pk])

        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.get(url)
        self.assertEqual([rule["pk"] for rule in response.json()], [self.acr1.pk])

    def test_get_accessrules_calendar_not_owned(self):
        """Listing rules of a calendar the user doesn't own is refused."""
        url = reverse("api:access-rule-list", args=[self.calendar2.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_create_accessrule(self):
        self.client.force_authenticate(self.admin_account)
        url = reverse("api:access-rule-list", args=[self.calendar2.pk])
        response = self.client.post(
            url, data=self._rule_data(self.account.mailbox), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["calendar"], self.calendar2.pk)
        self.assertTrue(
            models.AccessRule.objects.filter(
                mailbox=self.account.mailbox, calendar=self.calendar2
            ).exists()
        )

    def test_create_accessrule_simple_user(self):
        """A simple user can share a calendar with a mailbox of their domain."""
        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.post(
            url, data=self._rule_data(self.account2.mailbox), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            models.AccessRule.objects.filter(
                mailbox=self.account2.mailbox, calendar=self.calendar
            ).exists()
        )

    def test_create_accessrule_own_mailbox(self):
        """The calendar owner can't be a recipient."""
        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.post(
            url, data=self._rule_data(self.account.mailbox), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("mailbox", response.json())

    def test_create_accessrule_inactive_account(self):
        """A disabled account can't be a recipient."""
        self.account2.is_active = False
        self.account2.save()
        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.post(
            url, data=self._rule_data(self.account2.mailbox), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("mailbox", response.json())

    def test_create_accessrule_admin_other_domain(self):
        """An admin can't share a personal calendar outside their domain."""
        self.client.force_authenticate(self.admin_account)
        other_mbox = admin_models.Mailbox.objects.get(
            address="user", domain__name="test2.com"
        )
        url = reverse("api:access-rule-list", args=[self.calendar2.pk])
        response = self.client.post(
            url, data=self._rule_data(other_mbox), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("mailbox", response.json())

    def test_create_accessrule_duplicate(self):
        """A mailbox can only have one rule per calendar."""
        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.post(
            url, data=self._rule_data(self.admin_account.mailbox), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("mailbox", response.json())

    def test_create_accessrule_denied_mailbox(self):
        """Try to create an access rule with a mailbox the user doesn't own."""
        other_mbox = admin_models.Mailbox.objects.get(
            address="user", domain__name="test2.com"
        )
        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.post(
            url, data=self._rule_data(other_mbox), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_create_accessrule_mailbox_not_found(self):
        """Try to create an access rule with a non-existent mailbox."""
        data = {
            "mailbox": {
                "pk": 99999,
                "full_address": "doesnotexist@test.com",
            },
            "read": True,
        }
        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("mailbox", response.json())

    def test_create_accessrule_denied_calendar(self):
        """Try to grant access to a calendar the user doesn't own."""
        # self.account owns self.calendar; self.calendar2 belongs to admin_account
        url = reverse("api:access-rule-list", args=[self.calendar2.pk])
        response = self.client.post(
            url, data=self._rule_data(self.account.mailbox, write=True), format="json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            models.AccessRule.objects.filter(
                mailbox=self.account.mailbox, calendar=self.calendar2
            ).exists()
        )

    def test_create_accessrule_calendar_in_body_ignored(self):
        """The calendar is taken from the URL, never from the body."""
        url = reverse("api:access-rule-list", args=[self.calendar.pk])
        response = self.client.post(
            url,
            data=self._rule_data(self.account2.mailbox, calendar=self.calendar2.pk),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["calendar"], self.calendar.pk)
        self.assertFalse(
            models.AccessRule.objects.filter(
                mailbox=self.account2.mailbox, calendar=self.calendar2
            ).exists()
        )

    def test_update_accessrule_denied_calendar(self):
        """Try to point an owned rule to a calendar the user doesn't own."""
        acr = factories.AccessRuleFactory(
            calendar=self.calendar,
            mailbox=self.account2.mailbox,
            read=True,
            write=False,
        )
        url = reverse("api:access-rule-detail", args=[self.calendar.pk, acr.pk])
        response = self.client.put(
            url,
            data=self._rule_data(
                self.account2.mailbox, write=True, calendar=self.calendar2.pk
            ),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        acr.refresh_from_db()
        self.assertEqual(acr.calendar, self.calendar)

    def test_rights_generation_excludes_forged_rule(self):
        """A rejected create must never reach the generated rights file."""
        url = reverse("api:access-rule-list", args=[self.calendar2.pk])
        self.client.post(
            url, data=self._rule_data(self.account.mailbox, write=True), format="json"
        )

        rights_file_path = tempfile.mktemp()
        self.set_global_parameter("rights_file_path", rights_file_path, app="calendars")
        try:
            management.call_command("generate_rights", verbosity=False)
            cfg = ConfigParser()
            with open(rights_file_path) as fpo:
                cfg.read_file(fpo)
        finally:
            if os.path.exists(rights_file_path):
                os.unlink(rights_file_path)
        # No section may grant the attacker mailbox access to the victim calendar
        forged = [
            section
            for section in cfg.sections()
            if cfg.get(section, "user", fallback="")
            == self.account.mailbox.full_address
            and cfg.get(section, "collection", fallback="") == self.calendar2.path
        ]
        self.assertEqual(forged, [])

    def test_update_accessrule(self):
        """Test access rule modification."""
        self.client.force_authenticate(self.admin_account)
        acr = factories.AccessRuleFactory(
            calendar=self.calendar2,
            mailbox=self.account.mailbox,
            read=True,
            write=False,
        )
        url = reverse("api:access-rule-detail", args=[self.calendar2.pk, acr.pk])
        response = self.client.put(
            url,
            data=self._rule_data(self.account.mailbox, read=False, write=True),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        acr.refresh_from_db()
        self.assertFalse(acr.read)
        self.assertTrue(acr.write)

    def test_update_accessrule_permission(self):
        """Try to modify an access rule the user does not own."""
        calendar = factories.UserCalendarFactory(mailbox=self.admin_account.mailbox)
        acr = factories.AccessRuleFactory(
            calendar=calendar, mailbox=self.account.mailbox, read=True, write=True
        )
        data = self._rule_data(self.account.mailbox, read=False, write=True)
        # Through the real parent calendar
        url = reverse("api:access-rule-detail", args=[calendar.pk, acr.pk])
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 404)
        # Through a calendar the user owns
        url = reverse("api:access-rule-detail", args=[self.calendar.pk, acr.pk])
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 404)

    def test_delete_accessrule(self):
        """Test access rule removal."""
        url = reverse("api:access-rule-detail", args=[self.calendar.pk, self.acr1.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(models.AccessRule.DoesNotExist):
            self.acr1.refresh_from_db()


class EventViewSetTestCase(TestDataMixin, ModoAPITestCase):
    """Event viewset tests."""

    def setUp(self):
        """Initiate test context."""
        patcher1 = mock.patch("caldav.DAVClient")
        self.client_mock = patcher1.start()
        self.client_mock.return_value = mocks.DAVClientMock()
        self.addCleanup(patcher1.stop)

        patcher2 = mock.patch("modoboa.calendars.backends.caldav_.Calendar")
        self.cal_mock = patcher2.start()
        self.cal_mock.return_value = mocks.Calendar(client=self.client_mock)
        self.addCleanup(patcher2.stop)

        self.client.force_authenticate(self.account)
        self.set_global_parameter("server_location", "http://localhost")
        mocks.ACTIONS.clear()

    def _saved_ics(self):
        """Return the iCalendar data saved on the fake server."""
        saved = [action for action in mocks.ACTIONS if action[0] == "add_event"]
        self.assertEqual(len(saved), 1)
        return saved[0][2]

    def test_get_user_events(self):
        """Test event(s) retrieval."""
        # FIXME: drf nested routers does not handle reverse() properly
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/{1234}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["title"].startswith("Bastille"))

        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/"
        url = "{}?start={}&end={}".format(url, "20060712T182145Z", "20070712T182145Z")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_caldav_client_uses_preemptive_auth(self):
        """Credentials must be sent with the first request (no 401 round trip)."""
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/"
        url = "{}?start={}&end={}".format(url, "20060712T182145Z", "20070712T182145Z")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client_mock.call_args.kwargs["auth_type"], "basic")

    def test_get_user_events_wrong_calendar(self):
        url = f"/api/v2/user-calendars/{self.calendar2.pk}/events/"
        url = "{}?start={}&end={}".format(url, "20060712T182145Z", "20070712T182145Z")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_shared_events(self):
        """Test event(s) retrieval."""
        # FIXME: drf nested routers does not handle reverse() properly
        url = f"/api/v2/shared-calendars/{self.scalendar.pk}/events/{1234}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["title"].startswith("Bastille"))

        url = f"/api/v2/shared-calendars/{self.scalendar.pk}/events/"
        url = "{}?start={}&end={}".format(url, "20060712T182145Z", "20070712T182145Z")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_create_event(self):
        """Test event creation."""
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/"
        data = {
            "title": "Test event",
            "start_date": "2018-03-27",
            "end_date": "2018-03-28",
            "allDay": True,
            "color": "#ffdddd",
            "description": "Description",
            "calendar": self.calendar.pk,
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())

        url = f"/api/v2/shared-calendars/{self.scalendar.pk}/events/"
        data = {
            "title": "Test event 2",
            "start": "2018-03-27T00:00:00Z",
            "end": "2018-03-28T00:00:00Z",
            "allDay": False,
            "color": "#ffdddd",
            "description": "Description",
            "calendar": self.scalendar.pk,
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())

    def test_update_event(self):
        """Test event update."""
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/1234/"
        data = {
            "title": "Test event",
            "start_date": "2018-03-27",
            "end_date": "2018-03-28",
            "allDay": True,
            "color": "#ffdddd",
            "description": "Description",
            "calendar": self.calendar.pk,
            # "attendees": [{
            #     "display_name": "Test User",
            #     "email": "user@domain.test",
            # }]
        }
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", response.json())

    def test_patch_event(self):
        """Test event partial update."""
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/1234/"
        data = {
            "start_date": "2018-03-27",
            "end_date": "2018-03-28",
            "allDay": True,
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_move_event_between_cals(self):
        """Move an event."""
        data = {
            "title": "Test event",
            "start_date": "2018-03-27",
            "end_date": "2018-03-28",
            "allDay": True,
            "color": "#ffdddd",
            "description": "Description",
            "calendar": self.scalendar.pk,
            "new_calendar_type": "shared",
        }
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/1234/"
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_delete_event(self):
        """Test event deletion."""
        url = f"/api/v2/shared-calendars/{self.scalendar.pk}/events/1234/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

    def test_get_events_expands_recurrences(self):
        """Occurrences of a recurring event are returned with their id."""
        occurrence = mocks.EV_RECURRING.replace(
            "RRULE:FREQ=WEEKLY;COUNT=5", "RECURRENCE-ID:20260901T080000Z"
        )
        self.cal_mock.return_value.search = mock.Mock(
            return_value=[Event(data=occurrence, parent=self.cal_mock.return_value)]
        )
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/"
        url = f"{url}?start=2026-09-01T00:00:00Z&end=2026-09-30T00:00:00Z"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.cal_mock.return_value.search.call_args.kwargs["expand"])
        self.assertEqual(
            response.json()[0]["recurrence_id"], "2026-09-01T08:00:00+00:00"
        )

    def test_get_events_without_recurrence(self):
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/"
        url = "{}?start={}&end={}".format(url, "20060712T182145Z", "20070712T182145Z")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()[0]["recurrence_id"])

    def test_patch_occurrence(self):
        """Modify only one occurrence of a recurring event."""
        self.cal_mock.return_value.event_data = mocks.EV_RECURRING
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/weekly-1/"
        data = {
            "title": "Moved meeting",
            "start": "2026-09-08T14:00:00Z",
            "end": "2026-09-08T15:00:00Z",
            "recurrence_id": "2026-09-08T08:00:00+00:00",
            "scope": "occurrence",
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        ics = self._saved_ics()
        # The series is untouched, an override is added
        self.assertIn("DTSTART:20260901T080000Z", ics)
        self.assertIn("SUMMARY:Weekly meeting", ics)
        self.assertIn("RECURRENCE-ID:20260908T080000Z", ics)
        self.assertIn("DTSTART:20260908T140000Z", ics)
        self.assertIn("SUMMARY:Moved meeting", ics)

    def test_patch_series(self):
        """Moving an occurrence with series scope moves the whole series."""
        self.cal_mock.return_value.event_data = mocks.EV_RECURRING
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/weekly-1/"
        data = {
            "title": "Later meeting",
            "start": "2026-09-15T09:00:00Z",
            "end": "2026-09-15T10:30:00Z",
            "recurrence_id": "2026-09-15T08:00:00+00:00",
            "scope": "series",
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        ics = self._saved_ics()
        self.assertIn("DTSTART:20260901T090000Z", ics)
        self.assertIn("DTEND:20260901T103000Z", ics)
        self.assertIn("SUMMARY:Later meeting", ics)
        self.assertNotIn("RECURRENCE-ID", ics)

    def test_patch_series_all_day_status(self):
        self.cal_mock.return_value.event_data = mocks.EV_RECURRING
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/weekly-1/"
        data = {
            "allDay": True,
            "start_date": "2026-09-15",
            "end_date": "2026-09-15",
            "recurrence_id": "2026-09-15T08:00:00+00:00",
            "scope": "series",
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(mocks.ACTIONS, [])

    def test_patch_all_day_event_keeps_duration(self):
        """End date of all day events is inclusive in the API."""
        self.cal_mock.return_value.event_data = mocks.EV_ALLDAY
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/allday-1/"
        data = {
            "title": "Renamed",
            "allDay": True,
            "start_date": "2026-09-02",
            "end_date": "2026-09-02",
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        ics = self._saved_ics()
        self.assertIn("DTSTART;VALUE=DATE:20260902", ics)
        self.assertIn("DTEND;VALUE=DATE:20260903", ics)

    def test_patch_recurrence_requires_scope(self):
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/weekly-1/"
        data = {
            "start": "2026-09-08T14:00:00Z",
            "end": "2026-09-08T15:00:00Z",
            "recurrence_id": "2026-09-08T08:00:00+00:00",
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("scope", response.json())

    def test_patch_invalid_recurrence_id(self):
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/weekly-1/"
        data = {
            "start": "2026-09-08T14:00:00Z",
            "end": "2026-09-08T15:00:00Z",
            "recurrence_id": "not a date",
            "scope": "occurrence",
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("recurrence_id", response.json())

    def test_move_occurrence_to_other_calendar_denied(self):
        calendar = factories.UserCalendarFactory(
            name="Other", mailbox=self.calendar.mailbox
        )
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/weekly-1/"
        data = {
            "start": "2026-09-08T14:00:00Z",
            "end": "2026-09-08T15:00:00Z",
            "recurrence_id": "2026-09-08T08:00:00+00:00",
            "scope": "occurrence",
            "calendar": calendar.pk,
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("calendar", response.json())
        self.assertEqual(mocks.ACTIONS, [])

    def test_move_event_saves_before_delete(self):
        """The event must be saved in the new calendar before its removal."""
        calendar = factories.UserCalendarFactory(
            name="Other", mailbox=self.calendar.mailbox
        )
        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/1234/"
        data = {
            "start": "2018-03-27T10:00:00Z",
            "end": "2018-03-27T11:00:00Z",
            "calendar": calendar.pk,
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [action[0] for action in mocks.ACTIONS], ["add_event", "delete"]
        )

    def test_delete_occurrence(self):
        """Deleting one occurrence adds an EXDATE to the series."""
        self.cal_mock.return_value.event_data = mocks.EV_RECURRING
        url = (
            f"/api/v2/user-calendars/{self.calendar.pk}/events/weekly-1/"
            "?recurrence_id=2026-09-08T08:00:00%2B00:00&scope=occurrence"
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        ics = self._saved_ics()
        self.assertIn("EXDATE:20260908T080000Z", ics)
        self.assertNotIn("delete", [action[0] for action in mocks.ACTIONS])

    def test_delete_series(self):
        url = (
            f"/api/v2/user-calendars/{self.calendar.pk}/events/weekly-1/"
            "?recurrence_id=2026-09-08T08:00:00%2B00:00&scope=series"
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([action[0] for action in mocks.ACTIONS], ["delete"])

    def test_shared_events_own_domain(self):
        """A simple user can use events of a shared calendar in its domain."""
        url = f"/api/v2/shared-calendars/{self.scalendar.pk}/events/"
        url = "{}?start={}&end={}".format(url, "20060712T182145Z", "20070712T182145Z")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_shared_events_cross_domain_denied(self):
        """A simple user cannot reach a shared calendar from another domain."""
        # self.account is a simple user in test.com, scalendar2 lives in test2.com
        base = f"/api/v2/shared-calendars/{self.scalendar2.pk}/events"

        url = "{}/?start={}&end={}".format(base, "20060712T182145Z", "20070712T182145Z")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        url = f"{base}/1234/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        data = {
            "title": "Test event",
            "start_date": "2018-03-27",
            "end_date": "2018-03-28",
            "allDay": True,
            "color": "#ffdddd",
            "description": "Description",
            "calendar": self.scalendar.pk,
        }
        response = self.client.put(f"{base}/1234/", data=data, format="json")
        self.assertEqual(response.status_code, 404)

        # A valid payload is required to reach the authorization check
        response = self.client.patch(f"{base}/1234/", data=data, format="json")
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(f"{base}/1234/")
        self.assertEqual(response.status_code, 404)

    def test_shared_events_import_cross_domain_denied(self):
        """Importing into another domain's shared calendar is denied."""
        url = reverse("api:shared-event-import-from-file", args=[self.scalendar2.pk])
        path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "test_data/events.ics"
        )
        self.set_global_parameter("max_ics_file_size", "2048")
        with open(path) as fp:
            response = self.client.post(url, {"ics_file": fp})
        self.assertEqual(response.status_code, 404)

    def test_import_from_file(self):
        """Check import feature."""
        url = reverse("api:user-event-import-from-file", args=[self.calendar.pk])
        path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "test_data/events.ics"
        )
        # File too big => fails
        self.set_global_parameter("max_ics_file_size", "1")
        with open(path) as fp:
            data = {"ics_file": fp}
            response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.set_global_parameter("max_ics_file_size", "2048")
        with open(path) as fp:
            data = {"ics_file": fp}
            response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["counter"], 2)


class AttendeeViewSetTestCase(ModoAPITestCase):
    """Attendee viewset test case."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        populate_database()
        cls.account = core_models.User.objects.get(username="user@test.com")

    def setUp(self):
        """Initiate test context."""
        self.client.force_authenticate(self.account)

    def test_get_attendees(self):
        """Test attendees retrieval."""
        url = reverse("api:attendee-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class MailboxViewSetTestCase(ModoAPITestCase):
    """Mailbox viewset test case."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        populate_database()
        cls.account = core_models.User.objects.get(username="user@test.com")

    def setUp(self):
        """Initiate test context."""
        self.client.force_authenticate(self.account)

    def test_get_mailboxes(self):
        """Test mailbox retrieval."""
        url = reverse("api:mailbox-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class RenameDuplicateCalendarsMigrationTestCase(TransactionTestCase):
    """Migration renaming calendars before names become unique."""

    databases = "__all__"
    migrate_from = ("calendars", "0007_calendar_name_validator")
    migrate_to = ("calendars", "0009_calendar_name_unique_constraints")

    def get_targets(self, executor, node):
        """Return migration targets: node for calendars, latest for others."""
        return [node] + [
            leaf for leaf in executor.loader.graph.leaf_nodes() if leaf[0] != node[0]
        ]

    def setUp(self):
        executor = MigrationExecutor(connection)
        targets = self.get_targets(executor, self.migrate_from)
        executor.migrate(targets)
        executor.loader.build_graph()
        apps = executor.loader.project_state(targets).apps
        Domain = apps.get_model("admin", "Domain")
        Mailbox = apps.get_model("admin", "Mailbox")
        User = apps.get_model("core", "User")
        UserCalendar = apps.get_model("calendars", "UserCalendar")
        domain = Domain.objects.create(name="migration.test", quota=0)
        user = User.objects.create(username="user@migration.test")
        mailbox = Mailbox.objects.create(
            address="user", domain=domain, user=user, quota=0
        )
        for name in ["Work", "work", "Work", "Work (2)", "Home"]:
            UserCalendar.objects.create(
                mailbox=mailbox, name=name, _path=f"user@migration.test/{name}"
            )

    def tearDown(self):
        # Leave the database fully migrated for other tests
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_duplicates_are_renamed(self):
        executor = MigrationExecutor(connection)
        targets = self.get_targets(executor, self.migrate_to)
        executor.migrate(targets)
        executor.loader.build_graph()
        apps = executor.loader.project_state(targets).apps
        UserCalendar = apps.get_model("calendars", "UserCalendar")
        calendars = UserCalendar.objects.order_by("pk").values_list("name", "_path")
        self.assertEqual(
            list(calendars),
            [
                ("Work", "user@migration.test/Work"),
                ("work (3)", "user@migration.test/work"),
                ("Work (4)", "user@migration.test/Work"),
                ("Work (2)", "user@migration.test/Work (2)"),
                ("Home", "user@migration.test/Home"),
            ],
        )

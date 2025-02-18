"""Radicale extension unit tests."""

import os
import tempfile
from unittest import mock

from configparser import ConfigParser

from django.urls import reverse
from django.core import management

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core import factories as core_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoTestCase, ModoAPITestCase

from modoboa.admin.factories import populate_database

from . import factories
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


class AccessRuleTestCase(ModoTestCase):

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

        factories.AccessRuleFactory(
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
        section = "user@test.com-to-User calendar 0-acr"
        self.assertTrue(cfg.has_section(section))
        self.assertEqual(cfg.get(section, "user"), "user@test.com")
        self.assertEqual(
            cfg.get(section, "collection"), "admin@test.com/User calendar 0"
        )
        self.assertEqual(cfg.get(section, "permissions"), "r")

        # Call a second time
        management.call_command("generate_rights", verbosity=False)

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
        self.client.force_login(self.account)
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
        self.client.force_login(self.admin_account)
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
        self.client.force_login(self.account)

    def test_get_accessrules(self):
        """Test access rule retrieval."""
        url = reverse("api:access-rule-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_create_accessrule(self):
        data = {
            "mailbox": {
                "pk": self.account2.mailbox.pk,
                "full_address": self.account2.mailbox.full_address,
            },
            "read": True,
            "calendar": self.calendar.pk,
        }
        url = reverse("api:access-rule-list")
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_update_accessrule(self):
        """Test access rule modification."""
        data = {
            "mailbox": {
                "pk": self.admin_account.mailbox.pk,
                "full_address": self.admin_account.email,
            },
            "calendar": self.calendar.pk,
            "read": False,
            "write": True,
        }
        url = reverse("api:access-rule-detail", args=[self.acr1.pk])
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.acr1.refresh_from_db()
        self.assertFalse(self.acr1.read)

    def test_update_accessrule_permission(self):
        """Try to modify an access rule the user does not own."""
        calendar = factories.UserCalendarFactory(mailbox=self.admin_account.mailbox)
        acr = factories.AccessRuleFactory(
            calendar=calendar, mailbox=self.account.mailbox, read=True, write=True
        )
        data = {
            "mailbox": self.account.mailbox.pk,
            "calendar": calendar.pk,
            "read": False,
            "write": True,
        }
        url = reverse("api:access-rule-detail", args=[acr.pk])
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 404)

    def test_delete_accessrule(self):
        """Test access rule removal."""
        url = reverse("api:access-rule-detail", args=[self.acr1.pk])
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

        patcher2 = mock.patch("caldav.Calendar")
        self.cal_mock = patcher2.start()
        self.cal_mock.return_value = mocks.Calendar(client=self.client_mock)
        self.addCleanup(patcher2.stop)

        self.client.force_login(self.account)
        self.set_global_parameter("server_location", "http://localhost")

    def test_get_user_events(self):
        """Test event(s) retrieval."""
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

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

    def test_get_shared_events(self):
        """Test event(s) retrieval."""
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

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
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/"
        data = {
            "title": "Test event",
            "start": "2018-03-27T00:00:00Z",
            "end": "2018-03-28T00:00:00Z",
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
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/1234/"
        data = {
            "title": "Test event",
            "start": "2018-03-27T00:00:00Z",
            "end": "2018-03-28T00:00:00Z",
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
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

        url = f"/api/v2/user-calendars/{self.calendar.pk}/events/1234/"
        data = {
            "start": "2018-03-27T00:00:00Z",
            "end": "2018-03-28T00:00:00Z",
            "allDay": True,
        }
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_move_event_between_cals(self):
        """Move an event."""
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)
        data = {
            "title": "Test event",
            "start": "2018-03-27T00:00:00Z",
            "end": "2018-03-28T00:00:00Z",
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
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)

        url = f"/api/v2/shared-calendars/{self.scalendar.pk}/events/1234/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

    def test_import_from_file(self):
        """Check import feature."""
        data = {"username": "user@test.com", "password": "toto"}
        self.client.post(reverse("core:login"), data)
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
        self.client.force_login(self.account)

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
        self.client.force_login(self.account)

    def test_get_mailboxes(self):
        """Test mailbox retrieval."""
        url = reverse("api:mailbox-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

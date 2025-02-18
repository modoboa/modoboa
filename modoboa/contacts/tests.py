"""Contacts backend tests."""

import os

import httmock

from django.core import management

from django.urls import reverse
from django.utils import timezone

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase, ModoTestCase

from . import factories
from . import mocks
from . import models


class TestDataMixin:
    """Create some data."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()
        cls.user = core_models.User.objects.get(username="user@test.com")
        cls.addressbook = cls.user.addressbook_set.first()
        cls.category = factories.CategoryFactory(user=cls.user, name="Family")
        cls.contact = factories.ContactFactory(
            addressbook=cls.addressbook,
            emails=["homer@simpson.com"],
            phone_numbers=["01234567889"],
        )
        factories.ContactFactory(
            addressbook=cls.addressbook,
            first_name="Marge",
            emails=["marge@simpson.com"],
            categories=[cls.category],
        )
        factories.ContactFactory(
            addressbook=cls.addressbook, first_name="Bart", emails=["bart@simpson.com"]
        )

    def setUp(self, *args, **kwargs):
        """Initiate test context."""
        self.client.force_login(self.user)
        self.set_global_parameter(
            "server_location", "http://example.test/radicale/", app="calendars"
        )

    def enable_cdav_sync(self):
        """Enable sync. for user."""
        url = reverse("v2:parameter-user-detail", args=["contacts"])
        with httmock.HTTMock(mocks.options_mock, mocks.mkcol_mock):
            response = self.client.put(
                url,
                {
                    "enable_carddav_sync": True,
                    "sync_frequency": 300,
                },
                format="json",
            )
        self.assertEqual(response.status_code, 200)


class ViewsTestCase(TestDataMixin, ModoAPITestCase):
    """Check views."""

    def test_user_settings(self):
        """Check that remote collection creation request is sent."""
        # 1. Addressbook with contacts must be synced manually
        data = {"username": self.user.username, "password": "toto"}
        self.client.post(reverse("core:login"), data)
        self.enable_cdav_sync()
        self.addressbook.refresh_from_db()
        self.assertIs(self.addressbook.last_sync, None)

        # 2. Addressbook with no contacts can be considered synced
        user = core_models.User.objects.get(username="user@test2.com")
        abook = user.addressbook_set.first()
        data = {"username": user.username, "password": "toto"}
        self.client.post(reverse("core:login"), data)
        abook.refresh_from_db()
        self.assertIs(abook.last_sync, None)
        # Now enable sync.
        self.enable_cdav_sync()
        abook.refresh_from_db()
        self.assertIsNot(abook.last_sync, None)


class AddressBookViewSetTestCase(TestDataMixin, ModoAPITestCase):
    """Address book ViewSet tests."""

    def test_default(self):
        """Test default endpoint."""
        response = self.client.get(reverse("api:addressbook-default"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Contacts")

    def test_sync_to_cdav(self):
        """Test sync to CardDAV endpoint."""
        data = {"username": self.user.username, "password": "toto"}
        response = self.client.post(reverse("core:login"), data)
        self.enable_cdav_sync()
        with httmock.HTTMock(
            mocks.options_mock, mocks.mkcol_mock, mocks.put_mock, mocks.propfind_mock
        ):
            response = self.client.get(reverse("api:addressbook-sync-to-cdav"))
        self.assertEqual(response.status_code, 200)
        abook = self.user.addressbook_set.first()
        self.assertIsNot(abook.sync_token, None)
        contact = abook.contact_set.first()
        self.assertIsNot(contact.etag, None)

    def test_sync_from_cdav(self):
        """Test sync from CardDAV endpoint."""
        data = {"username": self.user.username, "password": "toto"}
        response = self.client.post(reverse("core:login"), data)
        self.enable_cdav_sync()
        self.user.addressbook_set.update(last_sync=timezone.now())
        with httmock.HTTMock(mocks.options_mock, mocks.report_mock, mocks.get_mock):
            response = self.client.get(reverse("api:addressbook-sync-from-cdav"))
        self.assertEqual(response.status_code, 200)


class CategoryViewSetTestCase(TestDataMixin, ModoAPITestCase):
    """Category ViewSet tests."""

    def test_get_categories(self):
        """Check category list endpoint."""
        url = reverse("api:category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create_category(self):
        """Create a new category."""
        url = reverse("api:category-list")
        data = {"name": "Amitiés"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_update_category(self):
        """Update a category."""
        url = reverse("api:category-detail", args=[self.category.pk])
        data = {"name": "Test"}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Test")

    def test_delete_category(self):
        """Try to delete a category."""
        url = reverse("api:category-detail", args=[self.category.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(models.Category.DoesNotExist):
            self.category.refresh_from_db()


class ContactViewSetTestCase(TestDataMixin, ModoAPITestCase):
    """Contact ViewSet tests."""

    def test_contact_list(self):
        """Check contact list endpoint."""
        url = reverse("api:contact-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(f"{url}?search=homer")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_category(self):
        """Check filtering."""
        url = reverse("api:contact-list")
        response = self.client.get(f"{url}?category={self.category.name}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create_contact(self):
        """Create a new contact."""
        data = {"username": self.user.username, "password": "toto"}
        response = self.client.post(reverse("core:login"), data)
        self.enable_cdav_sync()
        self.user.addressbook_set.update(last_sync=timezone.now())
        data = {
            "first_name": "Magie",
            "last_name": "Simpson",
            "emails": [{"address": "magie@simpson.com", "type": "home"}],
            "phone_numbers": [{"number": "+33123456789", "type": "home"}],
        }
        url = reverse("api:contact-list")
        with httmock.HTTMock(mocks.options_mock, mocks.put_mock):
            response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        contact = models.Contact.objects.get(pk=response.data["pk"])
        self.assertEqual(contact.emails.first().address, "magie@simpson.com")
        self.assertEqual(
            contact.phone_numbers.first().number,
            response.data["phone_numbers"][0]["number"],
        )
        self.assertEqual(contact.display_name, "Magie Simpson")
        self.assertIsNot(contact.etag, None)

    def test_create_contact_quick(self):
        """Create a contact with minimal information."""
        data = {"emails": [{"address": "magie@simpson.com", "type": "home"}]}
        url = reverse("api:contact-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["display_name"][0], "Name or display name required"
        )

        data["display_name"] = "Magie Simpson"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_contact_with_category(self):
        """Create a new contact with a category."""
        data = {
            "first_name": "Magie",
            "last_name": "Simpson",
            "emails": [{"address": "magie@simpson.com", "type": "home"}],
            "categories": [self.category.pk],
        }
        url = reverse("api:contact-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        contact = models.Contact.objects.get(pk=response.data["pk"])
        self.assertEqual(contact.categories.first(), self.category)

    def test_update_contact(self):
        """Update existing contact."""
        data = {"username": self.user.username, "password": "toto"}
        self.client.post(reverse("core:login"), data)
        self.enable_cdav_sync()
        self.user.addressbook_set.update(last_sync=timezone.now())
        url = reverse("api:contact-detail", args=[self.contact.pk])
        email_pk = self.contact.emails.first().pk
        data = {
            "first_name": "Homer 1",
            "last_name": "Simpson",
            "emails": [
                {"address": "duff@simpson.com", "type": "work"},
                {"address": "homer@simpson.com", "type": "other"},
            ],
            "phone_numbers": [
                {"number": "+33123456789", "type": "home"},
                {"number": "01234567889", "type": "work"},
            ],
            "categories": [self.category.pk],
        }
        with httmock.HTTMock(mocks.options_mock, mocks.put_mock, mocks.report_mock):
            response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)

        self.contact.refresh_from_db()
        self.assertEqual(self.contact.first_name, "Homer 1")
        self.assertEqual(self.contact.emails.count(), 2)
        self.assertEqual(models.EmailAddress.objects.get(pk=email_pk).type, "other")
        self.assertEqual(self.contact.phone_numbers.count(), 2)
        self.assertEqual(self.contact.categories.first(), self.category)
        self.assertIsNot(self.contact.etag, None)

        data["emails"].pop(1)
        data["phone_numbers"].pop(1)
        with httmock.HTTMock(mocks.options_mock, mocks.put_mock, mocks.report_mock):
            response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contact.emails.count(), 1)
        self.assertEqual(self.contact.phone_numbers.count(), 1)

    def test_delete_contact(self):
        """Try to delete a contact."""
        data = {"username": self.user.username, "password": "toto"}
        response = self.client.post(reverse("core:login"), data)
        self.enable_cdav_sync()
        url = reverse("api:contact-detail", args=[self.contact.pk])
        with httmock.HTTMock(mocks.options_mock, mocks.delete_mock):
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(models.Contact.DoesNotExist):
            self.contact.refresh_from_db()


class EmailAddressViewSetTestCase(TestDataMixin, ModoAPITestCase):
    """EmailAddressViewSet tests."""

    def test_emails_list(self):
        """Check list endpoint."""
        url = reverse("api:emailaddress-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(f"{url}?search=homer")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(f"{url}?search=Marge")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(f"{url}?search=Simpson")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)


class ImportTestCase(TestDataMixin, ModoTestCase):

    def setUp(self):
        super().setUp()
        self.path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "test_data/outlook_export.csv"
        )
        self.wrong_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "test_data/unknown_export.csv"
        )

    def test_import_wrong_addressbook(self):
        with self.assertRaises(management.base.CommandError) as ctx:
            management.call_command("import_contacts", "error@test.com", self.path)
        self.assertEqual(
            str(ctx.exception), "Address Book for email 'error@test.com' not found"
        )

    def test_import_unknown_backend(self):
        with self.assertRaises(management.base.CommandError) as ctx:
            management.call_command("import_contacts", "user@test.com", self.wrong_path)
        self.assertEqual(str(ctx.exception), "Failed to detect backend to use")

    def test_import_from_outlook_auto(self):
        management.call_command("import_contacts", "user@test.com", self.path)
        address = models.EmailAddress.objects.get(address="toto@titi.com")
        models.PhoneNumber.objects.get(number="12345678")
        self.assertEqual(address.contact.first_name, "Toto Tata")
        self.assertEqual(address.contact.addressbook.user.email, "user@test.com")
        self.assertEqual(address.contact.address, "Street 1 Street 2")

    def test_import_from_outlook(self):
        management.call_command(
            "import_contacts",
            "user@test.com",
            self.path,
            backend="outlook",
        )
        address = models.EmailAddress.objects.get(address="toto@titi.com")
        models.PhoneNumber.objects.get(number="12345678")
        self.assertEqual(address.contact.first_name, "Toto Tata")
        self.assertEqual(address.contact.addressbook.user.email, "user@test.com")
        self.assertEqual(address.contact.address, "Street 1 Street 2")

    def test_import_and_carddav_sync(self):
        with httmock.HTTMock(mocks.options_mock, mocks.put_mock):
            management.call_command(
                "import_contacts",
                "user@test.com",
                self.path,
                carddav_password="Toto1234",
            )
        address = models.EmailAddress.objects.get(address="toto@titi.com")
        models.PhoneNumber.objects.get(number="12345678")
        self.assertEqual(address.contact.first_name, "Toto Tata")
        self.assertEqual(address.contact.addressbook.user.email, "user@test.com")
        self.assertEqual(address.contact.address, "Street 1 Street 2")

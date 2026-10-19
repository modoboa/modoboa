"""Contacts backend tests."""

import importlib
import os

import httmock
import requests
import vobject
from rq import SimpleWorker

from django.apps import apps as django_apps
from django.core import management
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import django_rq

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase

from . import factories
from . import mocks
from . import models
from . import tasks
from .lib.carddav import _safe_xml


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
        self.client.force_authenticate(self.user)
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

    def disable_cdav_sync(self):
        url = reverse("v2:parameter-user-detail", args=["contacts"])
        response = self.client.put(
            url,
            {
                "enable_carddav_sync": False,
                "sync_frequency": 300,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)


class ViewsTestCase(TestDataMixin, ModoAPITestCase):
    """Check views."""

    def test_user_settings(self):
        """Check that remote collection creation request is sent."""
        # 1. Addressbook with contacts must be synced manuelle
        self.client.force_authenticate(self.user)
        self.enable_cdav_sync()
        self.addressbook.refresh_from_db()
        self.assertIs(self.addressbook.last_sync, None)

        # 2. Addressbook with no contacts can be considered synced
        user = core_models.User.objects.get(username="user@test2.com")
        abook = user.addressbook_set.first()
        self.client.force_authenticate(user)
        abook.refresh_from_db()
        self.assertIs(abook.last_sync, None)
        # Now enable sync.
        self.enable_cdav_sync()
        abook.refresh_from_db()
        self.assertIsNot(abook.last_sync, None)
        # And disable sync.
        self.disable_cdav_sync()
        abook.refresh_from_db()
        self.assertIs(abook.last_sync, None)


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
        last_sync = timezone.now()
        self.user.addressbook_set.update(last_sync=last_sync)
        addressbook = self.user.addressbook_set.first()
        self.assertEqual(addressbook.sync_token, "")
        with httmock.HTTMock(mocks.options_mock, mocks.report_mock, mocks.get_mock):
            response = self.client.get(reverse("api:addressbook-sync-from-cdav"))
            queue = django_rq.get_queue("modoboa")
            worker = SimpleWorker([queue], connection=queue.connection)
            worker.work(burst=True)
        self.assertEqual(response.status_code, 200)
        addressbook.refresh_from_db()
        self.assertNotEqual(addressbook.sync_token, "")

    def test_sync_without_addressbook(self):
        self.client.force_authenticate(core_models.User.objects.get(username="admin"))
        for name in ["api:addressbook-sync-to-cdav", "api:addressbook-sync-from-cdav"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 404)


class SyncFromCDAVTestCase(TestDataMixin, ModoAPITestCase):
    """Check sync_addressbook_from_cdav task."""

    def test_sync_does_not_touch_other_addressbooks(self):
        other_abook = core_models.User.objects.get(
            username="user@test2.com"
        ).addressbook_set.first()
        updated = factories.ContactFactory(
            addressbook=other_abook, first_name="Lisa", filename="newcard.vcf"
        )
        deleted = factories.ContactFactory(
            addressbook=other_abook, filename="deletedcard.vcf"
        )
        with httmock.HTTMock(mocks.options_mock, mocks.report_mock, mocks.get_mock):
            tasks.sync_addressbook_from_cdav(self.addressbook.pk, "token")
        updated.refresh_from_db()
        self.assertEqual(updated.first_name, "Lisa")
        self.assertTrue(models.Contact.objects.filter(pk=deleted.pk).exists())
        self.assertTrue(
            self.addressbook.contact_set.filter(filename="newcard.vcf").exists()
        )

    def test_sync_deletes_by_filename(self):
        contact = factories.ContactFactory(
            addressbook=self.addressbook, filename="deletedcard.vcf"
        )
        with httmock.HTTMock(mocks.options_mock, mocks.report_mock, mocks.get_mock):
            tasks.sync_addressbook_from_cdav(self.addressbook.pk, "token")
        self.assertFalse(models.Contact.objects.filter(pk=contact.pk).exists())

    def test_sync_matches_legacy_contact_by_uid(self):
        """Contact whose filename differs from the remote one."""
        legacy = factories.ContactFactory(
            addressbook=self.addressbook, uid="newcard.vcf", filename="legacy.vcf"
        )
        with httmock.HTTMock(mocks.options_mock, mocks.report_mock, mocks.get_mock):
            tasks.sync_addressbook_from_cdav(self.addressbook.pk, "token")
        legacy.refresh_from_db()
        self.assertEqual(legacy.filename, "newcard.vcf")
        self.assertEqual(legacy.display_name, "Forrest Gump")
        self.assertEqual(
            self.addressbook.contact_set.filter(uid="newcard.vcf").count(), 1
        )

    def test_sync_releases_lock_on_error(self):
        @httmock.urlmatch(method="REPORT")
        def report_error_mock(url, request):
            return {"status_code": 500}

        with httmock.HTTMock(mocks.options_mock, report_error_mock):
            with self.assertRaises(requests.exceptions.HTTPError):
                tasks.sync_addressbook_from_cdav(self.addressbook.pk, "token")
        self.addressbook.refresh_from_db()
        self.assertFalse(self.addressbook.syncing)

    def test_sync_skipped_when_locked(self):
        self.user.addressbook_set.update(syncing=True)
        # No HTTP mock: any request would fail
        tasks.sync_addressbook_from_cdav(self.addressbook.pk, "token")
        self.addressbook.refresh_from_db()
        self.assertTrue(self.addressbook.syncing)
        self.assertEqual(self.addressbook.sync_token, "")


class VCardTestCase(TestDataMixin, ModoAPITestCase):
    """Check vCard conversions."""

    def test_new_contact_filename(self):
        contact = factories.ContactFactory(addressbook=self.addressbook)
        self.assertFalse(contact.uid.endswith(".vcf"))
        self.assertEqual(contact.filename, f"{contact.uid}.vcf")

    def test_set_filename_migration(self):
        migration = importlib.import_module(
            "modoboa.contacts.migrations.0010_contact_filename"
        )
        with_ext = factories.ContactFactory(addressbook=self.addressbook)
        without_ext = factories.ContactFactory(addressbook=self.addressbook)
        models.Contact.objects.filter(pk=with_ext.pk).update(uid="a.vcf", filename="")
        models.Contact.objects.filter(pk=without_ext.pk).update(uid="b", filename="")
        migration.set_filename(django_apps, None)
        with_ext.refresh_from_db()
        without_ext.refresh_from_db()
        self.assertEqual(with_ext.filename, "a.vcf")
        self.assertEqual(without_ext.filename, "b.vcf")

    def test_update_from_vcard(self):
        contact = self.contact
        contact.company = "Springfield Nuclear Plant"
        contact.note = "D'oh"
        contact.save()
        uid = contact.uid
        vcard = vobject.readOne(
            "BEGIN:VCARD\r\n"
            "VERSION:3.0\r\n"
            "N:Gump;Forrest,Alexander;;;\r\n"
            "FN:Forrest Gump\r\n"
            "BDAY:--0415\r\n"
            "CATEGORIES:Family,Shrimp\r\n"
            "TEL;TYPE=WORK;VOICE:(111) 555-1212\r\n"
            "EMAIL;TYPE=PREF,INTERNET:F@example.com\r\n"
            "END:VCARD\r\n"
        )
        contact.update_from_vcard(vcard)
        contact.refresh_from_db()
        self.assertEqual(contact.uid, uid)
        self.assertEqual(contact.first_name, "Forrest Alexander")
        self.assertEqual(contact.display_name, "Forrest Gump")
        self.assertEqual(contact.company, "")
        self.assertEqual(contact.note, "")
        self.assertIsNone(contact.birth_date)
        self.assertEqual(
            sorted(contact.categories.values_list("name", flat=True)),
            ["Family", "Shrimp"],
        )
        self.assertIn(self.category, contact.categories.all())
        self.assertEqual(
            list(contact.emails.values_list("address", "type")),
            [("f@example.com", "other")],
        )
        self.assertEqual(
            list(contact.phone_numbers.values_list("number", "type")),
            [("(111) 555-1212", "work")],
        )

    def test_update_from_vcard_truncates_long_values(self):
        vcard = vobject.readOne(
            "BEGIN:VCARD\r\n"
            "VERSION:3.0\r\n"
            f"N:Gump;{'x' * 50};;;\r\n"
            "FN:Forrest Gump\r\n"
            "END:VCARD\r\n"
        )
        self.contact.update_from_vcard(vcard)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.first_name, "x" * 30)

    def test_to_vcard_exports_categories(self):
        contact = models.Contact.objects.get(first_name="Marge")
        vcard = vobject.readOne(contact.to_vcard())
        self.assertEqual(vcard.categories.value, ["Family"])


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
        self.assertEqual(len(response.data["results"]), 3)

        response = self.client.get(f"{url}?search=homer")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_category(self):
        """Check filtering."""
        url = reverse("api:contact-list")
        response = self.client.get(f"{url}?category={self.category.name}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

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

    def test_create_contact_with_foreign_category(self):
        """Categories of other users are refused."""
        user = core_models.User.objects.get(username="user@test2.com")
        category = factories.CategoryFactory(user=user, name="Other")
        data = {
            "display_name": "Magie Simpson",
            "emails": [{"address": "magie@simpson.com", "type": "home"}],
            "categories": [category.pk],
        }
        response = self.client.post(reverse("api:contact-list"), data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("categories", response.data)

    def test_create_contact_without_addressbook(self):
        self.client.force_authenticate(core_models.User.objects.get(username="admin"))
        data = {
            "display_name": "Magie Simpson",
            "emails": [{"address": "magie@simpson.com", "type": "home"}],
        }
        response = self.client.post(reverse("api:contact-list"), data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_partial_update_keeps_categories(self):
        contact = models.Contact.objects.get(first_name="Marge")
        url = reverse("api:contact-detail", args=[contact.pk])
        response = self.client.patch(url, {"note": "Blue hair"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(contact.categories.all()), [self.category])

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

    def test_delete_contact_missing_on_server(self):
        """Contact never pushed (no etag) and unknown remotely."""
        data = {"username": self.user.username, "password": "toto"}
        self.client.post(reverse("core:login"), data)
        self.enable_cdav_sync()
        self.user.addressbook_set.update(last_sync=timezone.now())
        headers = {}

        @httmock.urlmatch(method="DELETE")
        def delete_404_mock(url, request):
            headers.update(request.headers)
            return {"status_code": 404}

        url = reverse("api:contact-detail", args=[self.contact.pk])
        with httmock.HTTMock(mocks.options_mock, delete_404_mock):
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertNotIn("If-Match", headers)
        self.assertFalse(models.Contact.objects.filter(pk=self.contact.pk).exists())


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


class ImportTestCase(TestDataMixin, ModoAPITestCase):
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


class CardDavSecurityTestCase(TestCase):
    """Verify that the CardDAV XML parser is hardened against XML attacks (#1556)."""

    def test_safe_xml_rejects_entity_expansion(self):
        """Entity definitions must not be resolved."""
        payload = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE foo [<!ENTITY xxe "INJECTED">]>'
            b"<root>&xxe;</root>"
        )
        element = _safe_xml(payload)
        self.assertIsNone(element.text)

    def test_safe_xml_parses_valid_document(self):
        """Valid XML must still parse correctly."""
        payload = b'<d:multistatus xmlns:d="DAV:"><d:response><d:href>/x</d:href></d:response></d:multistatus>'
        element = _safe_xml(payload)
        children = list(element.iterchildren())
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].tag, "{DAV:}response")

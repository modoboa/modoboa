"""Domain related test cases."""

import os
import shutil
import tempfile
from unittest import mock

import dns.resolver
from testfixtures import compare

from django.core.management import call_command
from django.urls import reverse
from django.utils.html import escape

from modoboa.core import factories as core_factories
from modoboa.core.models import User
from modoboa.core.tests.test_views import SETTINGS_SAMPLE
from modoboa.lib.tests import ModoTestCase
from modoboa.maillog import factories as ml_factories

from . import utils
from .. import factories
from ..models import Alias, Domain


class DomainTestCase(ModoTestCase):
    """Test case for Domain."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(DomainTestCase, cls).setUpTestData()
        factories.populate_database()

    def test_create(self):
        """Test the creation of a domain."""
        values = {
            "name": "pouet.com", "quota": 1000, "default_mailbox_quota": 100,
            "create_dom_admin": False, "type": "domain", "stepid": "step3"
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.name, "pouet.com")
        self.assertEqual(dom.quota, 1000)
        self.assertEqual(dom.default_mailbox_quota, 100)
        self.assertEqual(dom.enabled, False)
        self.assertFalse(dom.admins)

    def test_create_utf8(self):
        """Test the creation of a domain with non-ASCII characters."""
        values = {
            "name": "pouét.com", "quota": 1000, "default_mailbox_quota": 100,
            "create_dom_admin": False, "type": "domain", "stepid": "step3"
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        dom = Domain.objects.get(name=u"pouét.com")
        self.assertEqual(dom.name, u"pouét.com")
        self.assertEqual(dom.quota, 1000)
        self.assertEqual(dom.default_mailbox_quota, 100)
        self.assertEqual(dom.enabled, False)
        self.assertFalse(dom.admins)

    def test_create_with_template(self):
        """Test the creation of a domain with a template."""
        values = {
            "name": "pouet.com", "quota": 1000, "default_mailbox_quota": 100,
            "create_dom_admin": True, "dom_admin_username": "toto",
            "with_mailbox": True, "create_aliases": True, "type": "domain",
            "stepid": "step3"
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster@pouet.com")
        self.assertTrue(
            al.aliasrecipient_set.filter(r_mailbox=da.mailbox)
            .exists()
        )
        self.assertTrue(da.can_access(al))

        values = {
            "name": "pouet2.com", "quota": 1000, "default_mailbox_quota": 100,
            "create_dom_admin": True, "dom_admin_username": "postmaster",
            "create_aliases": True, "type": "domain", "stepid": "step3",
            "with_mailbox": True
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        self.assertTrue(
            User.objects.filter(username="postmaster@pouet2.com").exists())
        self.assertFalse(
            Alias.objects.filter(
                address="postmaster@pouet2.com", internal=False).exists())

    def test_create_with_template_and_random_password(self):
        """Test domain creation with administrator and random password."""
        values = {
            "name": "pouet.com", "quota": 1000, "default_mailbox_quota": 100,
            "create_dom_admin": True, "dom_admin_username": "toto",
            "with_mailbox": True, "create_aliases": True, "type": "domain",
            "stepid": "step3", "random_password": True
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        self.assertFalse(
            self.client.login(username="admin@pouet.com", password="password"))

    def test_create_with_template_and_no_mailbox(self):
        """Test domain creation with administrator but no mailbox."""
        values = {
            "name": "pouet.com", "quota": 1000, "default_mailbox_quota": 100,
            "create_dom_admin": True, "dom_admin_username": "toto",
            "with_mailbox": False, "create_aliases": True, "type": "domain",
            "stepid": "step3"
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        self.assertFalse(hasattr(da, "mailbox"))
        self.assertFalse(
            Alias.objects.filter(address="postmaster@pouet.com").exists())

    def test_create_with_template_and_empty_quota(self):
        """Test the creation of a domain with a template and no quota"""
        values = {
            "name": "pouet.com", "quota": 0, "default_mailbox_quota": 0,
            "create_dom_admin": True, "dom_admin_username": "toto",
            "create_aliases": True, "type": "domain", "stepid": "step3",
            "with_mailbox": True
        }
        self.ajax_post(
            reverse("admin:domain_add"),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster@pouet.com")
        self.assertTrue(
            al.aliasrecipient_set.filter(r_mailbox=da.mailbox)
            .exists()
        )
        self.assertTrue(da.can_access(al))

    def test_create_with_template_and_custom_password(self):
        """Test creation of a domain with a template and custom password."""
        password = "Toto1000"
        self.set_global_parameter("default_password", password, app="core")
        values = {
            "name": "pouet.com", "quota": 0, "default_mailbox_quota": 0,
            "create_dom_admin": True, "dom_admin_username": "toto",
            "create_aliases": True, "type": "domain", "stepid": "step3",
            "with_mailbox": True
        }
        self.ajax_post(
            reverse("admin:domain_add"),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster@pouet.com")
        self.assertTrue(
            al.aliasrecipient_set.filter(r_mailbox=da.mailbox)
            .exists()
        )
        self.assertTrue(da.can_access(al))
        self.assertTrue(
            self.client.login(username="toto@pouet.com", password=password))

    def test_quota_constraints(self):
        """Check quota constraints."""
        values = {
            "name": "pouet.com", "quota": 10, "default_mailbox_quota": 100,
            "create_dom_admin": True, "dom_admin_username": "toto",
            "create_aliases": True, "type": "domain", "stepid": "step3"
        }
        response = self.ajax_post(
            reverse("admin:domain_add"),
            values, status=400
        )
        self.assertEqual(
            response["form_errors"]["default_mailbox_quota"][0],
            "Cannot be greater than domain quota")

        dom = Domain.objects.get(name="test.com")
        values["name"] = dom.name
        values["quota"] = 10
        values["default_mailbox_quota"] = 100
        response = self.ajax_post(
            reverse("admin:domain_change", args=[dom.pk]),
            values, status=400
        )
        self.assertEqual(
            response["form_errors"]["default_mailbox_quota"][0],
            "Cannot be greater than domain quota")

    def test_create_using_default_quota(self):
        """Check that default value is used for creation."""
        self.set_global_parameter("default_domain_quota", 500)
        self.set_global_parameter("default_mailbox_quota", 50)
        response = self.client.get(reverse("admin:domain_add"))
        self.assertContains(response, "value=\"500\"")
        self.assertContains(response, "value=\"50\"")

    @mock.patch.object(dns.resolver.Resolver, "query")
    @mock.patch("socket.getaddrinfo")
    def test_create_and_check_mx(self, mock_getaddrinfo, mock_query):
        """Check for authorized MX record."""
        reseller = core_factories.UserFactory(
            username="reseller", groups=("Resellers", ))
        self.client.force_login(reseller)

        self.set_global_parameter("enable_admin_limits", False, app="limits")
        self.set_global_parameter("valid_mxs", "192.0.2.1 2001:db8::1")
        self.set_global_parameter("domains_must_have_authorized_mx", True)

        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        values = {
            "name": "no-mx.example.com", "quota": 0,
            "default_mailbox_quota": 0,
            "create_dom_admin": True, "dom_admin_username": "toto",
            "create_aliases": True, "type": "domain", "stepid": "step3",
            "with_mailbox": True
        }
        self.ajax_post(reverse("admin:domain_add"), values, 400)
        self.assertFalse(
            Domain.objects.filter(name=values["name"]).exists())

        values["name"] = "pouet.com"
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        self.ajax_post(reverse("admin:domain_add"), values)

    def test_modify(self):
        """Test the modification of a domain

        Rename 'test.com' domain to 'pouet.com'
        """
        values = {
            "name": "pouet.com", "quota": 1000, "default_mailbox_quota": 100,
            "type": "domain", "enabled": True
        }
        dom = Domain.objects.get(name="test.com")
        self.ajax_post(
            reverse("admin:domain_change", args=[dom.id]),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.name, "pouet.com")
        self.assertTrue(dom.enabled)

        # Check if aliases were renamed too
        self.assertTrue(
            dom.alias_set.filter(address="postmaster@pouet.com").exists())

    def test_delete(self):
        """Test the removal of a domain."""
        dom = Domain.objects.get(name="test.com")
        self.ajax_post(reverse("admin:domain_delete", args=[dom.id]))
        with self.assertRaises(Domain.DoesNotExist):
            Domain.objects.get(pk=1)
        self.assertTrue(
            User.objects.filter(username="user@test.com").exists())
        self.set_global_parameter("auto_account_removal", True)
        dom = Domain.objects.get(name="test2.com")
        self.ajax_post(reverse("admin:domain_delete", args=[dom.id]))
        with self.assertRaises(Domain.DoesNotExist):
            Domain.objects.get(pk=1)
        self.assertFalse(
            User.objects.filter(username="admin@test2.com").exists())

    def test_domain_counters(self):
        """Check counters at domain level."""
        domain = Domain.objects.get(name="test.com")
        self.assertEqual(domain.domainalias_count, 0)
        self.assertEqual(domain.mailbox_count, 2)
        self.assertEqual(domain.mbalias_count, 3)
        self.assertEqual(domain.identities_count, 5)

    def test_domain_flat_list(self):
        """Test the 'domain_flat_list' view."""
        response = self.client.get(reverse("admin:domain_flat_list"))
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("test.com", content)
        self.assertIn("test2.com", content)

    def test_domain_detail_view(self):
        """Test Domain detail view."""
        self.set_global_parameter("enable_domain_limits", False, app="limits")
        domain = Domain.objects.get(name="test.com")
        url = reverse("admin:domain_detail", args=[domain.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Summary", response.content.decode())
        self.assertIn("Administrators", response.content.decode())
        self.assertIn("Usage", response.content.decode())
        self.assertNotIn("Resources usage", response.content.decode())
        self.set_global_parameter("enable_domain_limits", True, app="limits")
        response = self.client.get(url)
        self.assertIn("Resources usage", response.content.decode())

        # Try a domain with no quota
        domain = Domain.objects.filter(quota=0).first()
        url = reverse("admin:domain_detail", args=[domain.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Usage", response.content.decode())

        # Try with a fresh domain (see #1174)
        domain = factories.DomainFactory(name="simpson.com", quota=100)
        url = reverse("admin:domain_detail", args=[domain.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Usage", response.content.decode())

        user = User.objects.get(username="user@test.com")
        self.client.force_login(user)
        domain = Domain.objects.get(name="test2.com")
        url = reverse("admin:domain_detail", args=[domain.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_domain_quota_list_view(self):
        """Test quota list view."""
        factories.DomainFactory(name="test3.com", quota=100)
        url = reverse("admin:domain_quota_list")
        response = self.ajax_get(url)
        self.assertIn("50M", response["rows"])
        self.assertIn('title="40% (20 MB) allocated"', response["rows"])
        self.assertIn("test.com", response["rows"])

        old_rows = response["rows"]
        response = self.ajax_get("{}?sort_order=-name".format(url))
        self.assertNotEqual(old_rows, response["rows"])

        response = self.ajax_get("{}?sort_order=allocated_quota".format(url))
        self.assertNotEqual(old_rows, response["rows"])

    def test_domain_logs_list_view(self):
        """Test logs list view."""
        domain = Domain.objects.get(name="test.com")
        ml_factories.MaillogFactory(from_domain=domain)
        ml_factories.MaillogFactory(to_domain=domain, status="received")
        ml_factories.MaillogFactory()
        ml_factories.MaillogFactory()
        url = reverse("admin:domain_logs_list")
        response = self.ajax_get(url)
        self.assertIn("ID1", response["rows"])

        old_rows = response["rows"]
        response = self.ajax_get("{}?sort_order=-sender".format(url))
        self.assertNotEqual(old_rows, response["rows"])

        response = self.ajax_get("{}?searchquery=ID1".format(url))
        self.assertNotEqual(old_rows, response["rows"])

        admin = User.objects.get(username="admin@test.com")
        self.client.force_login(admin)
        url = reverse("admin:domain_logs_list")
        response = self.ajax_get(url)
        self.assertNotEqual(old_rows, response["rows"])

    def test_statitics_widget(self):
        """Test statistics display in dashboard."""
        url = reverse("core:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Global statistics", response.content.decode("utf-8"))

        self.client.force_login(
            User.objects.get(username="admin@test.com"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertNotIn("Global statistics", content)
        self.assertIn("Per-domain statistics", content)

    def test_page_loader(self):
        """Test page loader view."""
        factories.AlarmFactory(
            domain__name="test.com", mailbox=None, title="Test alarm")
        url = reverse("admin:domain_page")
        response = self.ajax_get(url)
        self.assertIn("handle_mailboxes", response)
        self.assertIn("listalarms", response["rows"])
        response = self.ajax_get("{}?objtype=quota".format(url))
        self.assertIn("progress-bar", response["rows"])


class DKIMTestCase(ModoTestCase):
    """Test case for DKIM."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(DKIMTestCase, cls).setUpTestData()
        factories.populate_database()

    def setUp(self):
        super(DKIMTestCase, self).setUp()
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_global_settings(self):
        """Check validation rules."""
        url = reverse("core:parameters")
        settings = SETTINGS_SAMPLE.copy()
        settings["admin-dkim_keys_storage_dir"] = "/wrong"
        response = self.client.post(url, settings, format="json")
        self.assertEqual(response.status_code, 400)
        compare(response.json(), {
            "form_errors": {"dkim_keys_storage_dir": ["Directory not found."]},
            "prefix": "admin"
        })
        settings["admin-dkim_keys_storage_dir"] = self.workdir
        response = self.client.post(url, settings, format="json")
        self.assertEqual(response.status_code, 200)

    def test_dkim_key_creation(self):
        """Test DKIM key creation."""
        values = {
            "name": "pouet.com", "quota": 1000, "default_mailbox_quota": 100,
            "create_dom_admin": False, "type": "domain", "stepid": "step3",
            "enable_dkim": True, "dkim_key_selector": ""
        }
        response = self.ajax_post(reverse("admin:domain_add"), values, 400)
        self.assertEqual(
            response["form_errors"]["enable_dkim"][0],
            "DKIM keys storage directory not configured")

        self.set_global_parameter("dkim_keys_storage_dir", self.workdir)
        response = self.ajax_post(reverse("admin:domain_add"), values, 400)
        self.assertEqual(
            response["form_errors"]["dkim_key_selector"][0],
            "This field is required.")

        values["dkim_key_selector"] = "default"
        self.ajax_post(reverse("admin:domain_add"), values)

        call_command("modo", "manage_dkim_keys")
        key_path = os.path.join(self.workdir, "{}.pem".format(values["name"]))
        self.assertTrue(os.path.exists(key_path))

        domain = Domain.objects.get(name=values["name"])
        url = reverse("admin:domain_detail", args=[domain.pk])
        response = self.client.get(url)
        self.assertContains(
            response, escape(domain.bind_format_dkim_public_key))

    def test_dkim_key_length_modification(self):
        """ """
        self.set_global_parameter("dkim_keys_storage_dir", self.workdir)
        values = {
            "name": "pouet.com", "quota": 1000, "default_mailbox_quota": 100,
            "create_dom_admin": False, "type": "domain", "stepid": "step3",
            "enable_dkim": True, "dkim_key_selector": "default"
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        call_command("modo", "manage_dkim_keys")
        key_path = os.path.join(self.workdir, "{}.pem".format(values["name"]))
        self.assertTrue(os.path.exists(key_path))
        dom = Domain.objects.get(name="pouet.com")
        values["dkim_key_length"] = 4096
        self.ajax_post(reverse("admin:domain_change", args=[dom.pk]), values)
        dom.refresh_from_db()
        self.assertEqual(dom.dkim_private_key_path, "")
        os.unlink(key_path)
        call_command("modo", "manage_dkim_keys")
        self.assertTrue(os.path.exists(key_path))

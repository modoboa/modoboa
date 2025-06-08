"""Test cases for the limits extension."""

from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.admin.models import Domain
from modoboa.core import factories as core_factories
from modoboa.core.models import User
from modoboa.lib import tests as lib_tests
from modoboa.limits.tests.test_user_limits import ResourceTestCase
from .. import utils


class DomainLimitsTestCase(ResourceTestCase):
    """Per-domain limits tests."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        lib_tests.ModoAPITestCase.setUpTestData()
        cls.localconfig.parameters.set_values(
            {"enable_admin_limits": False, "enable_domain_limits": True}
        )
        for name, _definition in utils.get_domain_limit_templates():
            cls.localconfig.parameters.set_value(f"deflt_domain_{name}_limit", 2)
        cls.localconfig.save()
        admin_factories.populate_database()

    def test_set_limits(self):
        """Try to set limits for a given domain."""
        domain = Domain.objects.get(name="test.com")
        values = {
            "name": domain.name,
            "quota": domain.quota,
            "default_mailbox_quota": domain.default_mailbox_quota,
            "enabled": domain.enabled,
            "type": "domain",
            "resources": [
                {"name": "mailboxes", "max_value": 3},
                {"name": "mailbox_aliases", "max_value": 3},
                {"name": "domain_aliases", "max_value": 3},
                {"name": "domain_admins", "max_value": 3},
            ],
        }
        response = self.client.put(
            reverse("v2:domain-detail", args=[domain.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        domain.refresh_from_db()
        self.assertEqual(
            domain.domainobjectlimit_set.get(name="mailboxes").max_value, 3
        )
        self.assertEqual(
            domain.domainobjectlimit_set.get(name="mailbox_aliases").max_value, 3
        )
        self.assertEqual(
            domain.domainobjectlimit_set.get(name="domain_aliases").max_value, 3
        )
        self.assertEqual(
            domain.domainobjectlimit_set.get(name="domain_admins").max_value, 3
        )

    def test_domain_aliases_limit(self):
        """Try to exceed defined limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="domain_aliases")
        self.assertFalse(limit.is_exceeded())
        url = reverse("v2:domain_alias-list")
        body = {"name": "domainalias1.net", "target": domain.id, "enabled": True}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 201)
        body["name"] = "domainalias2.net"
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 201)

        self.assertTrue(limit.is_exceeded())
        body["name"] = "domainalias3.net"
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["domain"], "Domain aliases: limit reached")

    def test_domain_admins_limit(self):
        """Try to exceed defined limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="domain_admins")
        self.assertFalse(limit.is_exceeded())
        user = User.objects.get(username="admin@test2.com")
        response = self.client.post(
            reverse("v2:domain-add-administrator", args=[domain.id]),
            {"account": user.id},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(limit.is_exceeded())
        user = core_factories.UserFactory(
            username="admin1000@test.com", groups=("DomainAdmins",)
        )
        response = self.client.post(
            reverse("v2:domain-add-administrator", args=[domain.id]),
            {"account": user.id},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_mailboxes_limit(self):
        """Try to exceed defined limits."""
        domain = Domain.objects.get(name="test.com")
        domain.domainobjectlimit_set.filter(name="mailboxes").update(max_value=3)
        limit = domain.domainobjectlimit_set.get(name="mailboxes")
        self.assertFalse(limit.is_exceeded())

        # Check if defined limit can't be exceeded
        username = "toto@test.com"
        self._create_account(username)
        self.assertTrue(limit.is_exceeded())
        self._create_account("titi@test.com", status=400)

        # Set unlimited value
        limit.max_value = -1
        limit.save(update_fields=["max_value"])
        self._create_account("titi@test.com")
        self.assertFalse(limit.is_exceeded())

    def test_mailbox_aliases_limit(self):
        """Try to exceed defined limits."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="mailbox_aliases")
        limit.max_value = 4
        limit.save()
        self.assertFalse(limit.is_exceeded())

        self._create_alias("alias1@test.com", ["user@test.com"])
        self.assertTrue(limit.is_exceeded())

        response = self._create_alias("alias2@test.com", ["user@test.com"], status=400)
        self.assertEqual(
            response.json()["address"][0], "Mailbox aliases: limit reached"
        )

        limit.max_value = 5
        limit.save()
        self._create_alias("forward2@test.com", ["user@test.com"])
        self.assertTrue(limit.is_exceeded())

        self._create_alias("forward3@test.com", ["user@test.com"], status=400)

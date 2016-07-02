# coding: utf-8
"""Test cases for the limits extension."""

from django.core.urlresolvers import reverse

from rest_framework.authtoken.models import Token

from modoboa.admin.factories import populate_database
from modoboa.admin.models import Domain
from modoboa.core import factories as core_factories
from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib import tests as lib_tests

from .. import utils


class APIAdminLimitsTestCase(lib_tests.ModoAPITestCase):
    """Check that limits are used also by the API."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(APIAdminLimitsTestCase, cls).setUpTestData()
        for name, tpl in utils.get_user_limit_templates():
            parameters.save_admin(
                "DEFLT_USER_{}_LIMIT".format(name.upper()), 2)
        populate_database()
        cls.user = User.objects.get(username="admin@test.com")
        cls.da_token = Token.objects.create(user=cls.user)
        cls.reseller = core_factories.UserFactory(
            username="reseller", groups=("Resellers", ),
        )
        cls.r_token = Token.objects.create(user=cls.reseller)

    def test_domadmins_limit(self):
        """Check domain admins limit."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.r_token.key)

        limit = self.reseller.userobjectlimit_set.get(name="domain_admins")
        url = reverse("external_api:account-list")
        data = {
            "username": "fromapi@test.com",
            "role": "DomainAdmins",
            "password": "Toto1234",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(limit.is_exceeded())

        data["username"] = "fromapi2@test.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(limit.is_exceeded())

        data["username"] = "fromapi3@test.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

        user = User.objects.get(username="user@test.com")
        domain = Domain.objects.get(name="test.com")
        domain.add_admin(self.reseller)
        url = reverse("external_api:account-detail", args=[user.pk])
        data = {
            "username": user.username,
            "role": "DomainAdmins",
            "password": "Toto1234",
            "mailbox": {
                "full_address": user.username,
                "quota": user.mailbox.quota
            }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_domains_limit(self):
        """Check domains limit."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.r_token.key)
        limit = self.reseller.userobjectlimit_set.get(name="domains")
        url = reverse("external_api:domain-list")
        data = {"name": "test3.com", "quota": 10}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(limit.is_exceeded())

        data["name"] = "test4.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(limit.is_exceeded())

        data["username"] = "test5.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_domain_aliases_limit(self):
        """Check domain aliases limit."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.r_token.key)
        domain = Domain.objects.get(name="test.com")
        domain.add_admin(self.reseller)
        limit = self.reseller.userobjectlimit_set.get(name="domain_aliases")
        url = reverse("external_api:domain_alias-list")
        data = {"name": "dalias1.com", "target": domain.pk}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(limit.is_exceeded())

        data["name"] = "dalias2.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(limit.is_exceeded())

        data["username"] = "dalias3.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_mailboxes_limit(self):
        """Check mailboxes limit."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.da_token.key)

        limit = self.user.userobjectlimit_set.get(name="mailboxes")
        url = reverse("external_api:account-list")
        data = {
            "username": "fromapi@test.com",
            "role": "SimpleUsers",
            "password": "Toto1234",
            "mailbox": {
                "full_address": "fromapi@test.com",
                "quota": 10
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(limit.is_exceeded())

        data["username"] = "fromapi2@test.com"
        data["mailbox"]["full_address"] = "fromapi2@test.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(limit.is_exceeded())

        data["username"] = "fromapi3@test.com"
        data["mailbox"]["full_address"] = "fromapi3@test.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_aliases_limit(self):
        """Check mailbox aliases limit."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.da_token.key)

        limit = self.user.userobjectlimit_set.get(name="mailbox_aliases")
        url = reverse("external_api:alias-list")
        data = {
            "address": "alias_fromapi@test.com",
            "recipients": [
                "user@test.com", "postmaster@test.com", "user_éé@nonlocal.com"
            ]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(limit.is_exceeded())

        data["address"] = "alias_fromapi2@test.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(limit.is_exceeded())

        data["address"] = "alias_fromapi3@test.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)


class APIDomainLimitsTestCase(lib_tests.ModoAPITestCase):
    """Check that limits are used also by the API."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(APIDomainLimitsTestCase, cls).setUpTestData()
        parameters.save_admin("ENABLE_DOMAIN_LIMITS", "yes")
        for name, tpl in utils.get_domain_limit_templates():
            parameters.save_admin(
                "DEFLT_DOMAIN_{}_LIMIT".format(name.upper()), 2)
        populate_database()

    def test_mailboxes_limit(self):
        """Check mailboxes limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="mailboxes")
        self.assertTrue(limit.is_exceeded())
        url = reverse("external_api:account-list")
        data = {
            "username": "fromapi@test.com",
            "role": "SimpleUsers",
            "password": "Toto1234",
            "mailbox": {
                "full_address": "fromapi@test.com",
                "quota": 10
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_domain_aliases_limit(self):
        """Check domain_aliases limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="domain_aliases")
        url = reverse("external_api:domain_alias-list")
        data = {"name": "dalias1.com", "target": domain.pk}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        data["name"] = "dalias2.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(limit.is_exceeded())
        data["name"] = "dalias3.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_mailbox_aliases_limit(self):
        """Check mailbox_aliases limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="mailbox_aliases")
        self.assertTrue(limit.is_exceeded())
        url = reverse("external_api:alias-list")
        data = {
            "address": "alias_fromapi@test.com",
            "recipients": [
                "user@test.com", "postmaster@test.com", "user_éé@nonlocal.com"
            ]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

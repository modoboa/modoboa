"""Test cases for the limits extension."""

from testfixtures import compare

from django.urls import reverse

from rest_framework.authtoken.models import Token

from modoboa.admin.factories import populate_database
from modoboa.admin.models import Domain
from modoboa.core import factories as core_factories
from modoboa.core.models import User
from modoboa.lib import permissions, tests as lib_tests
from .. import utils


class APIAdminLimitsTestCase(lib_tests.ModoAPITestCase):
    """Check that limits are used also by the API."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(APIAdminLimitsTestCase, cls).setUpTestData()
        for name, _definition in utils.get_user_limit_templates():
            cls.localconfig.parameters.set_value(
                "deflt_user_{0}_limit".format(name), 2)
        cls.localconfig.save()
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
            HTTP_AUTHORIZATION="Token " + self.r_token.key)

        limit = self.reseller.userobjectlimit_set.get(name="domain_admins")
        url = reverse("api:account-list")
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
        url = reverse("api:account-detail", args=[user.pk])
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
            HTTP_AUTHORIZATION="Token " + self.r_token.key)
        limit = self.reseller.userobjectlimit_set.get(name="domains")
        quota = self.reseller.userobjectlimit_set.get(name="quota")
        quota.max_value = 3
        quota.save(update_fields=["max_value"])
        url = reverse("api:domain-list")
        data = {"name": "test3.com", "quota": 1}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(limit.is_exceeded())
        self.assertFalse(quota.is_exceeded())

        data["name"] = "test4.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(limit.is_exceeded())
        self.assertFalse(quota.is_exceeded())

        data["name"] = "test5.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.content.decode("utf-8"), '"Domains: limit reached"'
        )

        self.client.delete(
            reverse("api:domain-detail",
                    args=[Domain.objects.get(name="test4.com").pk]))
        data["quota"] = 0
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content.decode(),
            '"You\'re not allowed to define unlimited values"')

    def test_domain_aliases_limit(self):
        """Check domain aliases limit."""
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.r_token.key)
        domain = Domain.objects.get(name="test.com")
        domain.add_admin(self.reseller)
        limit = self.reseller.userobjectlimit_set.get(name="domain_aliases")
        url = reverse("api:domain_alias-list")
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
            HTTP_AUTHORIZATION="Token " + self.da_token.key)

        limit = self.user.userobjectlimit_set.get(name="mailboxes")
        url = reverse("api:account-list")
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
            HTTP_AUTHORIZATION="Token " + self.da_token.key)

        limit = self.user.userobjectlimit_set.get(name="mailbox_aliases")
        url = reverse("api:alias-list")
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
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(APIDomainLimitsTestCase, cls).setUpTestData()
        cls.localconfig.parameters.set_value(
            "enable_domain_limits", True)
        for name, _definition in utils.get_domain_limit_templates():
            cls.localconfig.parameters.set_value(
                "deflt_domain_{0}_limit".format(name), 2)
        cls.localconfig.save()
        populate_database()

    def test_mailboxes_limit(self):
        """Check mailboxes limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="mailboxes")
        self.assertTrue(limit.is_exceeded())
        url = reverse("api:account-list")
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
        url = reverse("api:domain_alias-list")
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
        url = reverse("api:alias-list")
        data = {
            "address": "alias_fromapi@test.com",
            "recipients": [
                "user@test.com", "postmaster@test.com", "user_éé@nonlocal.com"
            ]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)


class ResourcesAPITestCase(lib_tests.ModoAPITestCase):
    """Check resources API."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(ResourcesAPITestCase, cls).setUpTestData()
        for name, _definition in utils.get_user_limit_templates():
            cls.localconfig.parameters.set_value(
                "deflt_user_{0}_limit".format(name), 2)
        cls.localconfig.save()
        populate_database()
        cls.user = User.objects.get(username="admin@test.com")
        cls.da_token = Token.objects.create(user=cls.user)
        cls.reseller = core_factories.UserFactory(
            username="reseller", groups=("Resellers", ),
        )
        cls.r_token = Token.objects.create(user=cls.reseller)

    def test_get_admin_resources(self):
        """Retrieve admin resources."""
        url = reverse("api:resources-detail", args=[self.user.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        expected = {
            "quota": 2,
            "mailboxes": 2,
            "domain_admins": 2,
            "domain_aliases": 2,
            "domains": 2,
            "mailbox_aliases": 2
        }
        compare(expected, response.data)

        # As reseller => fails
        self.client.credentials(
            HTTP_AUTHORIZATION="Token {}".format(self.r_token.key))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # As domain admin => fails
        self.client.credentials(
            HTTP_AUTHORIZATION="Token {}".format(self.da_token.key))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_update_resources(self):
        """Update resources."""
        url = reverse("api:resources-detail", args=[self.reseller.pk])
        response = self.client.get(url)
        resources = response.data
        resources.update({"domains": 1000, "mailboxes": 1000})
        response = self.client.put(url, resources)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.reseller.userobjectlimit_set.get(name="domains").max_value,
            1000)

        # As domain admin => fails
        self.client.credentials(
            HTTP_AUTHORIZATION="Token {}".format(self.da_token.key))
        resources.update({"domains": 2, "mailboxes": 2})
        url = reverse("api:resources-detail", args=[self.user.pk])
        response = self.client.put(url, resources)
        self.assertEqual(response.status_code, 404)

        # As reseller => ok
        permissions.grant_access_to_object(self.reseller, self.user, True)
        self.client.credentials(
            HTTP_AUTHORIZATION="Token {}".format(self.r_token.key))
        resources.update({"domains": 500, "mailboxes": 500})
        url = reverse("api:resources-detail", args=[self.user.pk])
        response = self.client.put(url, resources)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.user.userobjectlimit_set.get(name="domains").max_value,
            500)
        self.assertEqual(
            self.reseller.userobjectlimit_set.get(name="domains").max_value,
            502)
        resources.update({"domains": 1003})
        response = self.client.put(url, resources)
        self.assertEqual(response.status_code, 424)

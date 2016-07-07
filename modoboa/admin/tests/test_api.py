# coding: utf-8
"""Admin API related tests."""

import copy
import json

from django.core.urlresolvers import reverse

from rest_framework.authtoken.models import Token

from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
from modoboa.lib import parameters
from modoboa.lib.tests import ModoAPITestCase

from .. import factories
from .. import models


class DomainAPITestCase(ModoAPITestCase):
    """Check API."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(DomainAPITestCase, cls).setUpTestData()
        factories.populate_database()
        cls.da_token = Token.objects.create(
            user=core_models.User.objects.get(username="admin@test.com"))

    def test_get_domains(self):
        """Retrieve a list of domains."""
        url = reverse("external_api:domain-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        domain = response.data[0]
        url = reverse(
            "external_api:domain-detail", args=[domain["pk"]])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], domain["name"])

    def test_create_domain(self):
        """Check domain creation."""
        url = reverse("external_api:domain-list")
        response = self.client.post(url, {"name": "test3.com", "quota": 10})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            models.Domain.objects.filter(name="test3.com").exists())
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.data)
        self.assertIn("quota", response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.da_token.key)
        response = self.client.post(url, {"name": "test4.com", "quota": 10})
        self.assertEqual(response.status_code, 403)

    def test_update_domain(self):
        """Check domain update."""
        domain = models.Domain.objects.get(name="test.com")
        models.Mailbox.objects.filter(
            domain__name="test.com", address="user").update(
                use_domain_quota=True)
        url = reverse("external_api:domain-detail", args=[domain.pk])
        response = self.client.put(url, {"name": "test.com", "quota": 1000})
        self.assertEqual(response.status_code, 200)
        domain.refresh_from_db()
        self.assertEqual(domain.quota, 1000)
        mb = models.Mailbox.objects.get(
            domain__name="test.com", address="user")
        self.assertEqual(mb.quota, 1000)

        response = self.client.put(url, {"name": "test42.com", "quota": 1000})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            models.Mailbox.objects.filter(
                address="user", domain__name="test42.com").exists())

    def test_delete_domain(self):
        """Try to delete a domain."""
        domain = models.Domain.objects.get(name="test.com")
        url = reverse("external_api:domain-detail", args=[domain.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(models.Domain.objects.filter(pk=domain.pk).exists())


class DomainAliasAPITestCase(ModoAPITestCase):
    """Check DomainAlias API."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(DomainAliasAPITestCase, cls).setUpTestData()
        factories.populate_database()
        cls.dom_alias1 = factories.DomainAliasFactory(
            name="dalias1.com", target__name="test.com")
        cls.dom_alias2 = factories.DomainAliasFactory(
            name="dalias2.com", target__name="test2.com")
        cls.da_token = Token.objects.create(
            user=core_models.User.objects.get(username="admin@test.com"))

    def test_get(self):
        """Retrieve a list of domain aliases."""
        url = reverse("external_api:domain_alias-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        url = reverse(
            "external_api:domain_alias-detail", args=[response.data[0]["pk"]])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "dalias1.com")

        url = reverse("external_api:domain_alias-list")
        response = self.client.get("{}?domain=test.com".format(url))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.da_token.key)
        response = self.client.get(reverse("external_api:domain_alias-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_post(self):
        """Try to create a new domain alias."""
        url = reverse("external_api:domain_alias-list")
        target = models.Domain.objects.get(name="test.com")
        data = {
            "name": "dalias3.com",
            "target": target.pk
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

        dalias = json.loads(response.content)
        dalias = models.DomainAlias.objects.filter(
            pk=dalias["pk"]).first()
        self.assertEqual(dalias.target, target)

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.da_token.key)
        response = self.client.post(
            url, {"name": "dalias4.com", "target": target.pk}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_put(self):
        """Try to update a domain alias."""
        dalias = models.DomainAlias.objects.get(name="dalias1.com")
        url = reverse("external_api:domain_alias-detail", args=[dalias.pk])
        data = {
            "name": "dalias3.com", "target": dalias.target.pk
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)

        dalias.refresh_from_db()
        self.assertEqual(dalias.name, "dalias3.com")
        self.assertTrue(dalias.enabled)

    def test_delete(self):
        """Try to delete an existing domain alias."""
        dalias = models.DomainAlias.objects.get(name="dalias1.com")
        url = reverse("external_api:domain_alias-detail", args=[dalias.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            models.DomainAlias.objects.filter(pk=dalias.pk).exists())


class AccountAPITestCase(ModoAPITestCase):
    """Check Account API."""

    ACCOUNT_DATA = {
        "username": "fromapi@test.com",
        "role": "SimpleUsers",
        "password": "Toto1234",
        "mailbox": {
            "full_address": "fromapi@test.com",
            "quota": 10
        }
    }

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(AccountAPITestCase, cls).setUpTestData()
        factories.populate_database()
        cls.da_token = Token.objects.create(
            user=core_models.User.objects.get(username="admin@test.com"))

    def setUp(self):
        """Test setup."""
        super(AccountAPITestCase, self).setUp()
        parameters.save_admin("ENABLE_ADMIN_LIMITS", "no", app="limits")
        parameters.save_admin("ENABLE_DOMAIN_LIMITS", "no", app="limits")

    def test_get_accounts(self):
        """Retrieve a list of accounts."""
        url = reverse("external_api:account-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 5)

        response = self.client.get("{}?domain=test.com".format(url))
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 2)

        response = self.client.get("{}?domain=pouet.com".format(url))
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 0)

    def test_create_account(self):
        """Try to create a new account."""
        url = reverse("external_api:account-list")
        response = self.client.post(url, self.ACCOUNT_DATA, format="json")
        self.assertEqual(response.status_code, 201)

        account = json.loads(response.content)
        user = core_models.User.objects.filter(pk=account["pk"]).first()
        self.assertIsNot(user, None)
        self.assertIsNot(user.mailbox, None)
        domadmin = core_models.User.objects.get(username="admin@test.com")
        self.assertTrue(domadmin.can_access(user))

        data = copy.deepcopy(self.ACCOUNT_DATA)
        data["username"] = "fromapi_ééé@test.com"
        data["mailbox"]["full_address"] = data["username"]
        url = reverse("external_api:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_domainadmin_account(self):
        """Try to create a domain admin."""
        data = copy.deepcopy(self.ACCOUNT_DATA)
        data["domains"] = ["test.com"]
        data["role"] = "DomainAdmins"
        url = reverse("external_api:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        domain = admin_models.Domain.objects.get(name="test.com")
        admin = core_models.User.objects.get(
            pk=json.loads(response.content)["pk"])
        self.assertIn(admin, domain.admins)

        data["username"] = "domain_admin"
        del data["mailbox"]
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_account_with_no_mailbox(self):
        """Try to create a new account."""
        data = copy.deepcopy(self.ACCOUNT_DATA)
        del data["mailbox"]
        url = reverse("external_api:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        account = json.loads(response.content)
        user = core_models.User.objects.filter(pk=account["pk"]).first()
        self.assertIsNot(user, None)
        self.assertIsNot(user.mailbox, None)
        self.assertEqual(user.mailbox.quota, user.mailbox.domain.quota)

    def test_create_existing_account(self):
        """Check if unicity is respected."""
        data = copy.deepcopy(self.ACCOUNT_DATA)
        data["username"] = "user@test.com"
        url = reverse("external_api:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

        data.update({"username": "domainadmin", "role": "DomainAdmins"})
        data["mailbox"]["full_address"] = "admin@test.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 409)

    def test_create_account_bad_password(self):
        """Try to create a new account."""
        data = copy.deepcopy(self.ACCOUNT_DATA)
        data["password"] = "toto"
        url = reverse("external_api:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        errors = json.loads(response.content)
        self.assertIn("password", errors)

    def test_create_account_as_domadmin(self):
        """As DomainAdmin, try to create a new account."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.da_token.key)
        data = copy.deepcopy(self.ACCOUNT_DATA)
        data["mailbox"]["quota"] = 20
        url = reverse("external_api:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        data["username"] = "fromapi@test2.com"
        data["mailbox"].update({"full_address": "fromapi@test2.com",
                                "quota": 10})
        url = reverse("external_api:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        errors = json.loads(response.content)
        self.assertIn("domain", errors)

    def test_create_account_bad_master_user(self):
        """Try to create a new account."""
        data = copy.deepcopy(self.ACCOUNT_DATA)
        data["master_user"] = True
        url = reverse("external_api:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        errors = json.loads(response.content)
        self.assertIn("master_user", errors)

    def test_update_account(self):
        """Try to update an account."""
        account = core_models.User.objects.get(username="user@test.com")
        url = reverse("external_api:account-detail", args=[account.pk])
        data = {
            "username": "fromapi@test.com",
            "role": account.role,
            "password": "Toto1234",
            "mailbox": {
                "full_address": "fromapi@test.com",
                "quota": account.mailbox.quota
            }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertEqual(account.email, account.mailbox.full_address)
        self.assertTrue(account.check_password("Toto1234"))

        del data["password"]
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertTrue(account.check_password("Toto1234"))

    def test_patch_account(self):
        """Try to patch an account."""
        account = core_models.User.objects.get(username="user@test.com")
        url = reverse("external_api:account-detail", args=[account.pk])
        data = {
            "username": "fromapi@test.com",
            "mailbox": {
                "full_address": "fromapi@test.com",
            }
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 405)

    def test_update_domain_admin_account(self):
        """Try to change administered domains."""
        account = core_models.User.objects.get(username="admin@test.com")
        url = reverse("external_api:account-detail", args=[account.pk])
        data = {
            "username": account.username,
            "role": account.role,
            "password": "Toto1234",
            "mailbox": {
                "full_address": account.mailbox.full_address,
                "quota": account.mailbox.quota
            },
            "domains": ["test.com", "test2.com"]
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        domains = admin_models.Domain.objects.get_for_admin(account)
        self.assertEqual(domains.count(), 2)
        self.assertTrue(domains.filter(name="test2.com").exists())

        data["domains"] = ["test2.com"]
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        domains = admin_models.Domain.objects.get_for_admin(account)
        self.assertEqual(domains.count(), 1)
        self.assertTrue(domains.filter(name="test2.com").exists())

    def test_update_account_wrong_address(self):
        """Try to update an account."""
        account = core_models.User.objects.get(username="user@test.com")
        url = reverse("external_api:account-detail", args=[account.pk])
        data = {
            "username": "fromapi@test3.com",
            "role": account.role,
            "password": "Toto1234",
            "mailbox": {
                "full_address": "fromapi@test3.com",
                "quota": account.mailbox.quota
            }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 404)

    def test_delete_account(self):
        """Try to delete an account."""
        account = core_models.User.objects.get(username="user@test.com")
        domadmin = core_models.User.objects.get(username="admin@test.com")
        self.assertTrue(domadmin.can_access(account))
        url = reverse("external_api:account-detail", args=[account.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            core_models.User.objects.filter(pk=account.pk).exists())
        self.assertFalse(domadmin.can_access(account))

    def test_account_exists(self):
        """Validate /exists/ service."""
        url = reverse("external_api:account-exists")
        response = self.client.get(
            "{}?email={}".format(url, "user@test.com"))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertTrue(content["exists"])
        response = self.client.get(
            "{}?email={}".format(url, "pipo@test.com"))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertFalse(content["exists"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_change_password(self):
        """Check the change password service."""
        account = core_models.User.objects.get(username="user@test.com")
        url = reverse(
            "external_api:account-password", args=[account.pk])
        response = self.client.put(
            url, {"password": "toto", "new_password": "pass"},
            format="json")
        # must fail because password is too weak
        self.assertEqual(response.status_code, 400)

        response = self.client.put(
            url, {"password": "toto", "new_password": "Toto1234"},
            format="json")
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertTrue(account.check_password("Toto1234"))


class AliasAPITestCase(ModoAPITestCase):
    """Check Alias API."""

    ALIAS_DATA = {
        "address": "alias_fromapi@test.com",
        "recipients": [
            "user@test.com", "postmaster@test.com", "user_éé@nonlocal.com"
        ]
    }

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(AliasAPITestCase, cls).setUpTestData()
        parameters.save_admin("ENABLE_ADMIN_LIMITS", "no", app="limits")
        factories.populate_database()
        cls.da_token = Token.objects.create(
            user=core_models.User.objects.get(username="admin@test.com"))

    def test_get_aliases(self):
        """Retrieve a list of aliases."""
        url = reverse("external_api:alias-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 3)

        response = self.client.get("{}?domain=test.com".format(url))
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(len(response), 3)

    def test_get_alias(self):
        """Retrieve an alias."""
        al = models.Alias.objects.get(address="alias@test.com")
        url = reverse("external_api:alias-detail", args=[al.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(response["recipients"], ["user@test.com"])

    def test_create_alias(self):
        """Try to create a new alias."""
        url = reverse("external_api:alias-list")
        response = self.client.post(url, self.ALIAS_DATA, format="json")
        self.assertEqual(response.status_code, 201)

        alias = json.loads(response.content)
        alias = models.Alias.objects.filter(pk=alias["pk"]).first()
        domadmin = core_models.User.objects.get(username="admin@test.com")
        self.assertTrue(domadmin.can_access(alias))
        self.assertEqual(alias.aliasrecipient_set.count(), 3)
        self.assertTrue(alias.aliasrecipient_set.filter(
            address="user@test.com", r_mailbox__isnull=False).exists())
        self.assertTrue(alias.aliasrecipient_set.filter(
            address="postmaster@test.com", r_alias__isnull=False).exists())
        self.assertTrue(alias.aliasrecipient_set.filter(
            address="user_éé@nonlocal.com",
            r_mailbox__isnull=True, r_alias__isnull=True).exists())

        # Create catchall alias
        data = copy.deepcopy(self.ALIAS_DATA)
        data["address"] = "@test.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_alias_as_domadmin(self):
        """As DomainAdmin, try to create a new alias."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.da_token.key)
        url = reverse("external_api:alias-list")
        response = self.client.post(url, self.ALIAS_DATA, format="json")
        self.assertEqual(response.status_code, 201)

        data = copy.deepcopy(self.ALIAS_DATA)
        data["address"] = "alias_fromapi@test2.com"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        errors = json.loads(response.content)
        self.assertIn("address", errors)

    def test_update_alias(self):
        """Try to update an alias."""
        alias = models.Alias.objects.get(address="alias@test.com")
        url = reverse("external_api:alias-detail", args=[alias.pk])
        data = {
            "address": "alias@test.com",
            "recipients": ["user@test.com", "user@nonlocal.com"]
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)

        alias.refresh_from_db()
        self.assertEqual(alias.aliasrecipient_set.count(), 2)
        data = {
            "address": "alias@test.com",
            "recipients": ["user@nonlocal.com"]
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        alias.refresh_from_db()
        self.assertEqual(alias.aliasrecipient_set.count(), 1)

        data = {
            "address": "alias@test.com",
            "recipients": []
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_delete_alias(self):
        """Try to delete an existing alias."""
        alias = models.Alias.objects.get(address="alias@test.com")
        domadmin = core_models.User.objects.get(username="admin@test.com")
        self.assertTrue(domadmin.can_access(alias))
        url = reverse("external_api:alias-detail", args=[alias.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            models.Alias.objects.filter(pk=alias.pk).exists())
        self.assertFalse(domadmin.can_access(alias))
        self.assertFalse(
            models.AliasRecipient.objects.filter(
                address="user@test.com", alias__address="alias@test.com")
            .exists()
        )

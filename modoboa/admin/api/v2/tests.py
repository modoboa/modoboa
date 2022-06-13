"""API v2 tests."""

from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils.encoding import force_text

from rest_framework.authtoken.models import Token

from modoboa.admin import factories, models
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase


class DomainViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()
        cls.da_token = Token.objects.create(
            user=core_models.User.objects.get(username="admin@test.com"))

    def test_create(self):
        url = reverse("v2:domain-list")
        data = {
            "name": "domain.tld",
            "domain_admin": {
                "username": "admin",
                "with_mailbox": True,
                "with_aliases": True
            }
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)

        dom = models.Domain.objects.get(pk=resp.json()["pk"])
        self.assertEqual(len(dom.admins), 1)
        admin = dom.admins.first()
        self.assertTrue(hasattr(admin, "mailbox"))
        self.assertTrue(
            models.Alias.objects.filter(
                address="postmaster@domain.tld").exists()
        )

    def test_update(self):
        domain = models.Domain.objects.get(name="test2.com")
        data = {
            "name": "test2.com",
            "type": "relaydomain",
            "transport": {
                "service": "relay",
                "settings": {
                    "relay_target_port": 25,
                    "relay_target_host": "localhost"
                }
            }
        }
        url = reverse("v2:domain-detail", args=[domain.pk])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        domain.refresh_from_db()
        self.assertEqual(domain.transport.service, data["transport"]["service"])
        self.assertEqual(
            domain.transport._settings["relay_target_host"],
            data["transport"]["settings"]["relay_target_host"]
        )

        data["transport"]["relay_verify_recipients"] = True
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_update_resources(self):
        self.set_global_parameter("enable_domain_limits", True, app="limits")
        domain = models.Domain.objects.get(name="test2.com")
        data = {
            "name": "test2.com",
            "resources": [
                {"name": "domain_aliases", "max_value": 20}
            ]
        }
        url = reverse("v2:domain-detail", args=[domain.pk])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            domain.domainobjectlimit_set.get(name="domain_aliases").max_value, 20
        )

    def test_delete(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.da_token.key)

        domain = models.Domain.objects.get(name="test2.com")
        url = reverse("v2:domain-delete", args=[domain.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)

        domain = models.Domain.objects.get(name="test.com")
        url = reverse("v2:domain-delete", args=[domain.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        url = reverse("v2:domain-delete", args=[domain.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

    def test_administrators(self):
        domain = models.Domain.objects.get(name="test.com")
        url = reverse("v2:domain-administrators", args=[domain.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_administrator(self):
        domain = models.Domain.objects.get(name="test.com")
        url = reverse("v2:domain-add-administrator", args=[domain.pk])
        account = core_models.User.objects.get(username="user@test.com")
        data = {"account": account.pk}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_remove_adminstrator(self):
        domain = models.Domain.objects.get(name="test.com")
        url = reverse("v2:domain-remove-administrator", args=[domain.pk])
        account = core_models.User.objects.get(username="user@test.com")
        data = {"account": account.pk}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_domains_import(self):
        f = ContentFile(b"""domain; domain1.com; 1000; 100; True
domain; domain2.com; 1000; 200; False
domainalias; domalias1.com; domain1.com; True
""", name="domains.csv")
        self.client.post(
            reverse("v2:domain-import-from-csv"), {
                "sourcefile": f
            }
        )
        admin = core_models.User.objects.get(username="admin")
        dom = models.Domain.objects.get(name="domain1.com")
        self.assertEqual(dom.quota, 1000)
        self.assertEqual(dom.default_mailbox_quota, 100)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(dom))
        domalias = models.DomainAlias.objects.get(name="domalias1.com")
        self.assertEqual(domalias.target, dom)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(domalias))
        dom = models.Domain.objects.get(name="domain2.com")
        self.assertEqual(dom.default_mailbox_quota, 200)
        self.assertFalse(dom.enabled)
        self.assertTrue(admin.is_owner(dom))

    def test_export_domains(self):
        """Check domain export."""
        dom = models.Domain.objects.get(name="test.com")
        factories.DomainAliasFactory(name="alias.test", target=dom)
        response = self.client.get(reverse("v2:domain-export"))
        expected_response = [
            "domain,test.com,50,10,True",
            "domainalias,alias.test,test.com,True",
            "domain,test2.com,0,0,True",
        ]
        self.assertCountEqual(
            expected_response,
            force_text(response.content.strip()).split("\r\n")
        )


class AccountViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_create(self):
        url = reverse("v2:account-list")
        data = {
            "username": "toto@test.com",
            "role": "SimpleUsers",
            "mailbox": {
                "use_domain_quota": True
            },
            "password": "Toto12345",
            "language": "fr",
            "aliases": ["alias3@test.com"]
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            models.Alias.objects.filter(
                address="alias3@test.com").exists()
        )

    def test_create_admin(self):
        url = reverse("v2:account-list")
        data = {
            "username": "superadmin",
            "role": "SuperAdmins",
            "password": "Toto12345",
            "language": "fr",
            "aliases": ["alias3@test.com"]
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_create_with_bad_password(self):
        url = reverse("v2:account-list")
        data = {
            "username": "superadmin",
            "role": "SuperAdmins",
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json())

        data["password"] = "Toto"
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json())

    def test_validate(self):
        data = {"username": "toto@test.com"}
        url = reverse("v2:account-validate")
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 204)

    def test_random_password(self):
        url = reverse("v2:account-random-password")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("password", resp.json())

    def test_delete(self):
        account = core_models.User.objects.get(username="user@test.com")
        url = reverse("v2:account-delete", args=[account.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)
        with self.assertRaises(core_models.User.DoesNotExist):
            account.refresh_from_db()

    def test_update(self):
        account = core_models.User.objects.get(username="user@test.com")
        url = reverse("v2:account-detail", args=[account.pk])
        data = {
            "username": "user@test.com",
            "role": "SimpleUsers",
            "password": "Toto12345",
            "mailbox": {
                "quota": 10
            }
        }
        resp = self.client.patch(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_update_admin(self):
        account = core_models.User.objects.get(username="admin")
        url = reverse("v2:account-detail", args=[account.pk])
        data = {
            "username": "superadmin@test.com",
            "role": "SuperAdmins",
            "password": "Toto12345",
            "mailbox": {
                "quota": 10
            }
        }
        resp = self.client.patch(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        account.refresh_from_db()
        self.assertEqual(account.email, data["username"])
        self.assertEqual(account.mailbox.full_address, data["username"])

    def test_update_resources(self):
        account = core_models.User.objects.get(username="admin@test.com")
        url = reverse("v2:account-detail", args=[account.pk])
        data = {
            "resources": [
                {"name": "mailboxes", "max_value": 10},
                {"name": "mailbox_aliases", "max_value": 10}
            ]
        }
        resp = self.client.patch(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        limit = account.userobjectlimit_set.get(name="mailboxes")
        self.assertEqual(limit.max_value, 10)

    def test_get_with_resources(self):
        account = core_models.User.objects.get(username="admin@test.com")
        url = reverse("v2:account-detail", args=[account.pk])
        resp = self.client.get(url, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["resources"]), 2)


class IdentityViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_list(self):
        url = reverse("v2:identities-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 8)

    def test_import(self):
        f = ContentFile("""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; 0
account; Truc@test.com; toto; René; Truc; True; DomainAdmins; truc@test.com; 5; test.com
alias; alias1@test.com; True; user1@test.com
forward; alias2@test.com; True; user1+ext@test.com
forward; fwd1@test.com; True; user@extdomain.com
dlist; dlist@test.com; True; user1@test.com; user@extdomain.com
""", name="identities.csv")  # NOQA:E501
        self.client.post(
            reverse("v2:identities-import-from-csv"),
            {"sourcefile": f, "crypt_password": True}
        )
        admin = core_models.User.objects.get(username="admin")
        u1 = core_models.User.objects.get(username="user1@test.com")
        mb1 = u1.mailbox
        self.assertTrue(admin.is_owner(u1))
        self.assertEqual(u1.email, "user1@test.com")
        self.assertEqual(u1.first_name, "User")
        self.assertEqual(u1.last_name, "One")
        self.assertTrue(u1.is_active)
        self.assertEqual(u1.role, "SimpleUsers")
        self.assertTrue(mb1.use_domain_quota)
        self.assertEqual(mb1.quota, 0)
        self.assertTrue(admin.is_owner(mb1))
        self.assertEqual(mb1.full_address, "user1@test.com")
        self.assertTrue(
            self.client.login(username="user1@test.com", password="toto")
        )

        da = core_models.User.objects.get(username="truc@test.com")
        damb = da.mailbox
        self.assertEqual(da.first_name, u"René")
        self.assertEqual(da.role, "DomainAdmins")
        self.assertEqual(damb.quota, 5)
        self.assertFalse(damb.use_domain_quota)
        self.assertEqual(damb.full_address, "truc@test.com")
        dom = models.Domain.objects.get(name="test.com")
        self.assertIn(da, dom.admins)
        u = core_models.User.objects.get(username="user@test.com")
        self.assertTrue(da.can_access(u))

        al = models.Alias.objects.get(address="alias1@test.com")
        self.assertTrue(
            al.aliasrecipient_set
            .filter(r_mailbox=u1.mailbox).exists()
        )
        self.assertTrue(admin.is_owner(al))

        fwd = models.Alias.objects.get(address="fwd1@test.com")
        self.assertTrue(
            fwd.aliasrecipient_set
            .filter(
                address="user@extdomain.com", r_mailbox__isnull=True,
                r_alias__isnull=True)
            .exists()
        )
        self.assertTrue(admin.is_owner(fwd))

        dlist = models.Alias.objects.get(address="dlist@test.com")
        self.assertTrue(
            dlist.aliasrecipient_set
            .filter(r_mailbox=u1.mailbox).exists()
        )
        self.assertTrue(
            dlist.aliasrecipient_set.filter(address="user@extdomain.com")
            .exists()
        )
        self.assertTrue(admin.is_owner(dlist))

    def test_export(self):
        response = self.client.get(reverse("v2:identities-export"))
        expected_response = "account,admin,,,,True,SuperAdmins,,\r\naccount,admin@test.com,{PLAIN}toto,,,True,DomainAdmins,admin@test.com,10,test.com\r\naccount,admin@test2.com,{PLAIN}toto,,,True,DomainAdmins,admin@test2.com,10,test2.com\r\naccount,user@test.com,{PLAIN}toto,,,True,SimpleUsers,user@test.com,10\r\naccount,user@test2.com,{PLAIN}toto,,,True,SimpleUsers,user@test2.com,10\r\nalias,alias@test.com,True,user@test.com\r\nalias,forward@test.com,True,user@external.com\r\nalias,postmaster@test.com,True,test@truc.fr,toto@titi.com\r\n"  # NOQA:E501
        received_content = force_text(response.content.strip()).split("\r\n")
        # Empty admin password because it is hashed using SHA512-CRYPT
        admin_row = received_content[0].split(",")
        admin_row[2] = ""
        received_content[0] = ",".join(admin_row)
        self.assertCountEqual(
            expected_response.strip().split("\r\n"),
            received_content
        )


class AliasViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_validate(self):
        url = reverse("v2:alias-validate")
        data = {"address": "alias@unknown.com"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)

        data = {"address": "alias@test.com"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)

        data = {"address": "alias2@test.com"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 204)

    def test_random_address(self):
        url = reverse("v2:alias-random-address")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("address", resp.json())


class UserAccountViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()
        cls.da = core_models.User.objects.get(username="admin@test.com")
        cls.da_token = Token.objects.create(user=cls.da)

    def test_forward(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.da_token.key)
        url = reverse("v2:account-forward")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("recipients", resp.json())

        data = {"recipients": "user@domain.ext"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.da.mailbox.aliasrecipient_set.count(), 1)

        data = {"recipients": "user@domain.ext", "keepcopies": True}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            models.Alias.objects.filter(address=self.da.username).count(),
            2
        )

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["keepcopies"])

        data = {"keepcopies": False}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            models.Alias.objects.filter(address=self.da.username).count(),
            1
        )


class AlarmViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()
        factories.AlarmFactory(
            domain__name="test.com", mailbox=None, title="Test alarm")

    def test_list(self):
        url = reverse("v2:alarm-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

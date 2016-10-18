# coding: utf-8
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse

from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib.tests import ModoTestCase

from .. import factories
from ..models import Domain, Alias, DomainAlias


class ImportTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(ImportTestCase, cls).setUpTestData()
        parameters.save_admin("ENABLE_ADMIN_LIMITS", "no", app="limits")
        factories.populate_database()

    def test_domains_import(self):
        f = ContentFile(b"""domain; domain1.com; 100; True
domain; domain2.com; 200; False
domainalias; domalias1.com; domain1.com; True
""", name="domains.csv")
        self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        admin = User.objects.get(username="admin")
        dom = Domain.objects.get(name="domain1.com")
        self.assertEqual(dom.quota, 100)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(dom))
        domalias = DomainAlias.objects.get(name="domalias1.com")
        self.assertEqual(domalias.target, dom)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(domalias))
        dom = Domain.objects.get(name="domain2.com")
        self.assertEqual(dom.quota, 200)
        self.assertFalse(dom.enabled)
        self.assertTrue(admin.is_owner(dom))

    def test_import_domains_with_conflict(self):
        f = ContentFile(b"""domain;test.alias;10;True
domainalias;test.alias;test.com;True
""", name="domains.csv")
        resp = self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        self.assertIn('Object already exists: domainalias', resp.content)

    def test_identities_import(self):
        f = ContentFile(b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; 0
account; truc@test.com; toto; René; Truc; True; DomainAdmins; truc@test.com; 5; test.com
alias; alias1@test.com; True; user1@test.com
forward; alias2@test.com; True; user1+ext@test.com
forward; fwd1@test.com; True; user@extdomain.com
dlist; dlist@test.com; True; user1@test.com; user@extdomain.com
""", name="identities.csv")
        self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        admin = User.objects.get(username="admin")
        u1 = User.objects.get(username="user1@test.com")
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

        da = User.objects.get(username="truc@test.com")
        damb = da.mailbox
        self.assertEqual(da.first_name, u"René")
        self.assertEqual(da.role, "DomainAdmins")
        self.assertEqual(damb.quota, 5)
        self.assertFalse(damb.use_domain_quota)
        self.assertEqual(damb.full_address, "truc@test.com")
        dom = Domain.objects.get(name="test.com")
        self.assertIn(da, dom.admins)
        u = User.objects.get(username="user@test.com")
        self.assertTrue(da.can_access(u))

        al = Alias.objects.get(address="alias1@test.com")
        self.assertTrue(
            al.aliasrecipient_set
            .filter(r_mailbox=u1.mailbox).exists()
        )
        self.assertTrue(admin.is_owner(al))

        fwd = Alias.objects.get(address="fwd1@test.com")
        self.assertTrue(
            fwd.aliasrecipient_set
            .filter(
                address="user@extdomain.com", r_mailbox__isnull=True,
                r_alias__isnull=True)
            .exists()
        )
        self.assertTrue(admin.is_owner(fwd))

        dlist = Alias.objects.get(address="dlist@test.com")
        self.assertTrue(
            dlist.aliasrecipient_set
            .filter(r_mailbox=u1.mailbox).exists()
        )
        self.assertTrue(
            dlist.aliasrecipient_set.filter(address="user@extdomain.com")
            .exists()
        )
        self.assertTrue(admin.is_owner(dlist))

    def test_import_for_nonlocal_domain(self):
        """Try to import an account for nonlocal domain."""
        f = ContentFile(b"""
account; user1@nonlocal.com; toto; User; One; True; SimpleUsers; user1@nonlocal.com; 0
""", name="identities.csv")
        self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        self.assertFalse(
            User.objects.filter(username="user1@nonlocal.com").exists())

    def test_import_invalid_quota(self):
        f = ContentFile(b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; ; test.com
""", name="identities.csv")
        resp = self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        self.assertIn('wrong quota value', resp.content)

    def test_import_domain_by_domainadmin(self):
        """Check if a domain admin is not allowed to import a domain."""
        self.client.logout()
        self.client.login(username="admin@test.com", password="toto")
        f = ContentFile(b"""
domain; domain2.com; 200; False
""", name="identities.csv")
        resp = self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        self.assertIn("You are not allowed to import domains", resp.content)
        f = ContentFile(b"""
domainalias; domalias1.com; test.com; True
""", name="identities.csv")
        resp = self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        self.assertIn(
            "You are not allowed to import domain aliases", resp.content)

    def test_import_quota_too_big(self):
        self.client.logout()
        self.client.login(username="admin@test.com", password="toto")
        f = ContentFile(b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; 20
""", name="identities.csv")
        resp = self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        self.assertIn('Quota is greater than the allowed', resp.content)

    def test_import_missing_quota(self):
        f = ContentFile(b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com
""", name="identities.csv")
        self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        account = User.objects.get(username="user1@test.com")
        self.assertEqual(
            account.mailbox.quota,
            account.mailbox.domain.quota
        )

    def test_import_duplicate(self):
        f = ContentFile(b"""
account; admin@test.com; toto; Admin; ; True; DomainAdmins; admin@test.com; 0; test.com
account; truc@test.com; toto; René; Truc; True; DomainAdmins; truc@test.com; 0; test.com
""", name="identities.csv")
        self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True,
             "continue_if_exists": True}
        )
        admin = User.objects.get(username="admin")
        u1 = User.objects.get(username="truc@test.com")
        self.assertTrue(admin.is_owner(u1))

    def test_import_superadmin(self):
        """Check if a domain admin can import a superadmin

        Expected result: no
        """
        self.client.logout()
        self.assertTrue(
            self.client.login(username="admin@test.com", password="toto")
        )
        f = ContentFile(b"""
account; sa@test.com; toto; Super; Admin; True; SuperAdmins; superadmin@test.com; 50
""", name="identities.csv")
        self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True,
             "continue_if_exists": True}
        )
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="sa@test.com")

    def test_import_alias_with_empty_values(self):
        f = ContentFile(b"""
alias;user.alias@test.com;True;user@test.com;;;;;;;;;;;;;;;;
""", name="identities.csv")
        self.client.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True,
             "continue_if_exists": True}
        )
        alias = Alias.objects.get(address="user.alias@test.com")
        self.assertEqual(alias.type, "alias")

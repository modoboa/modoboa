# coding: utf-8
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from modoboa.extensions.admin.models import (
    Domain, Alias, DomainAlias
)
from modoboa.extensions.admin import factories


class ImportTestCase(ModoTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(ImportTestCase, self).setUp()
        factories.populate_database()

    def test_domains_import(self):
        f = ContentFile(b"""domain; domain1.com; 100; True
domain; domain2.com; 200; False
domainalias; domalias1.com; domain1.com; True
""", name="domains.csv")
        self.clt.post(
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
        resp = self.clt.post(
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
forward; fwd1@test.com; True; user@extdomain.com
dlist; dlist@test.com; True; user1@test.com; user@extdomain.com
""", name="identities.csv")
        self.clt.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        admin = User.objects.get(username="admin")
        u1 = User.objects.get(username="user1@test.com")
        mb1 = u1.mailbox_set.all()[0]
        self.assertTrue(admin.is_owner(u1))
        self.assertEqual(u1.email, "user1@test.com")
        self.assertEqual(u1.first_name, "User")
        self.assertEqual(u1.last_name, "One")
        self.assertTrue(u1.is_active)
        self.assertEqual(u1.group, "SimpleUsers")
        self.assertTrue(mb1.use_domain_quota)
        self.assertEqual(mb1.quota, 0)
        self.assertTrue(admin.is_owner(mb1))
        self.assertEqual(mb1.full_address, "user1@test.com")
        self.assertTrue(self.clt.login(username="user1@test.com", password="toto"))

        da = User.objects.get(username="truc@test.com")
        damb = da.mailbox_set.all()[0]
        self.assertEqual(da.first_name, u"René")
        self.assertEqual(da.group, "DomainAdmins")
        self.assertEqual(damb.quota, 5)
        self.assertFalse(damb.use_domain_quota)
        self.assertEqual(damb.full_address, "truc@test.com")
        dom = Domain.objects.get(name="test.com")
        self.assertIn(da, dom.admins)
        u = User.objects.get(username="user@test.com")
        self.assertTrue(da.can_access(u))

        al = Alias.objects.get(address="alias1", domain__name="test.com")
        self.assertIn(u1.mailbox_set.all()[0], al.mboxes.all())
        self.assertTrue(admin.is_owner(al))

        fwd = Alias.objects.get(address="fwd1", domain__name="test.com")
        self.assertIn("user@extdomain.com", fwd.extmboxes)
        self.assertTrue(admin.is_owner(fwd))

        dlist = Alias.objects.get(address="dlist", domain__name="test.com")
        self.assertIn(u1.mailbox_set.all()[0], dlist.mboxes.all())
        self.assertIn("user@extdomain.com", dlist.extmboxes)
        self.assertTrue(admin.is_owner(dlist))

    def test_import_invalid_quota(self):
        f = ContentFile(b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; ; test.com
""", name="identities.csv")
        resp = self.clt.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        self.assertIn('wrong quota value', resp.content)

    def test_import_quota_too_big(self):
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        f = ContentFile(b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; 20
""", name="identities.csv")
        resp = self.clt.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        self.assertIn('Quota is greater than the allowed', resp.content)

    def test_import_missing_quota(self):
        f = ContentFile(b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com
""", name="identities.csv")
        resp = self.clt.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True}
        )
        account = User.objects.get(username="user1@test.com")
        self.assertEqual(
            account.mailbox_set.all()[0].quota,
            account.mailbox_set.all()[0].domain.quota
        )

    def test_import_duplicate(self):
        f = ContentFile(b"""
account; admin@test.com; toto; Admin; ; True; DomainAdmins; admin@test.com; 0; test.com
account; truc@test.com; toto; René; Truc; True; DomainAdmins; truc@test.com; 0; test.com
""", name="identities.csv")
        self.clt.post(
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
        self.clt.logout()
        self.assertTrue(self.clt.login(username="admin@test.com", password="toto"))
        f = ContentFile(b"""
account; sa@test.com; toto; Super; Admin; True; SuperAdmins; superadmin@test.com; 50
""", name="identities.csv")
        self.clt.post(
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
        self.clt.post(
            reverse("admin:identity_import"),
            {"sourcefile": f, "crypt_password": True,
             "continue_if_exists": True}
        )
        alias = Alias.objects.get(
            domain__name="test.com", address="user.alias"
        )
        self.assertEqual(alias.type, "alias")

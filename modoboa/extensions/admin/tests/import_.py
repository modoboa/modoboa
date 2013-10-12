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
            reverse("modoboa.extensions.admin.views.import.import_domains"), {
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

    def test_identities_import(self):
        f = ContentFile(b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com
account; truc@test.com; toto; René; Truc; True; DomainAdmins; truc@test.com; test.com
alias; alias1@test.com; True; user1@test.com
forward; fwd1@test.com; True; user@extdomain.com
dlist; dlist@test.com; True; user1@test.com; user@extdomain.com
""", name="identities.csv")
        self.clt.post(
            reverse("modoboa.extensions.admin.views.import.import_identities"),
            {"sourcefile": f, "crypt_password": True}
        )
        admin = User.objects.get(username="admin")
        u1 = User.objects.get(username="user1@test.com")
        self.assertTrue(admin.is_owner(u1))
        self.assertEqual(u1.email, "user1@test.com")
        self.assertEqual(u1.first_name, "User")
        self.assertEqual(u1.last_name, "One")
        self.assertTrue(u1.is_active)
        self.assertEqual(u1.group, "SimpleUsers")
        self.assertTrue(admin.is_owner(u1.mailbox_set.all()[0]))
        self.assertEqual(u1.mailbox_set.all()[0].full_address, "user1@test.com")
        self.assertTrue(self.clt.login(username="user1@test.com", password="toto"))

        da = User.objects.get(username="truc@test.com")
        self.assertEqual(da.first_name, u"René")
        self.assertEqual(da.group, "DomainAdmins")
        self.assertEqual(da.mailbox_set.all()[0].full_address, "truc@test.com")
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

    def test_import_duplicate(self):
        f = ContentFile(b"""
account; admin@test.com; toto; Admin; ; True; DomainAdmins; admin@test.com; test.com
account; truc@test.com; toto; René; Truc; True; DomainAdmins; truc@test.com; test.com
""", name="identities.csv")
        self.clt.post(
            reverse("modoboa.extensions.admin.views.import.import_identities"),
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
account; sa@test.com; toto; Super; Admin; True; SuperAdmins; superadmin@test.com
""", name="identities.csv")
        self.clt.post(
            reverse("modoboa.extensions.admin.views.import.import_identities"),
            {"sourcefile": f, "crypt_password": True,
             "continue_if_exists": True}
        )
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="sa@test.com")

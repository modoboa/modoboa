# coding: utf-8
"""
Basic tests for the 'admin' application
=======================================

TODO:

* Add new tests to check domain/mailbox manipulations when
  create_directories == yes

"""
import os
from django.test import TestCase
from django.test.client import Client
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from models import *
from modoboa.admin.lib import *
from modoboa.lib import parameters
from modoboa.lib.tests import ModoTestCase


class DomainTestCase(ModoTestCase):
    fixtures = ["initial_users.json", "test_content.json"]

    def test_create(self):
        """Test the creation of a domain
        """
        values = {
            "name": "pouet.com", "quota": 100, "create_dom_admin": "no",
            "stepid": 2
        }
        self.check_ajax_post(reverse("modoboa.admin.views.newdomain"), values)
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.name, "pouet.com")
        self.assertEqual(dom.quota, 100)
        self.assertEqual(dom.enabled, False)
        self.assertFalse(dom.admins)

    def test_create_with_template(self):
        """Test the creation of a domain with a template

        """
        values = {
            "name": "pouet.com", "quota": 100, "create_dom_admin": "yes",
            "dom_admin_username": "toto", "create_aliases": "yes",
            "stepid": 2
        }
        self.check_ajax_post(reverse("modoboa.admin.views.newdomain"), values)
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster", domain__name="pouet.com")
        self.assertIn(da.mailbox_set.all()[0], al.mboxes.all())
        self.assertTrue(da.can_access(al))

    def test_create_with_template_and_empty_quota(self):
        """Test the creation of a domain with a template and no quota"""
        values = {
            "name": "pouet.com", "quota": 0, "create_dom_admin": "yes",
            "dom_admin_username": "toto", "create_aliases": "yes",
            "stepid": 2
        }
        self.check_ajax_post(reverse("modoboa.admin.views.newdomain"), values)
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster", domain__name="pouet.com")
        self.assertIn(da.mailbox_set.all()[0], al.mboxes.all())
        self.assertTrue(da.can_access(al))

    def test_modify(self):
        """Test the modification of a domain

        Rename 'test.com' domain to 'pouet.com'
        """
        values = {
            "name": "pouet.com", "quota": 100, "enabled": True
        }
        self.check_ajax_post(reverse("modoboa.admin.views.editdomain", args=[1]), values)        
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.name, "pouet.com")
        self.assertTrue(dom.enabled)

    def test_delete(self):
        """Test the removal of a domain
        """
        self.check_ajax_get(reverse("modoboa.admin.views.deldomain", args=[1]), {})
        with self.assertRaises(Domain.DoesNotExist):
            Domain.objects.get(pk=1)


class DomainAliasTestCase(ModoTestCase):
    fixtures = ["initial_users.json", "test_content.json"]

    def test_model(self):
        dom = Domain.objects.get(name="test.com")
        domal = DomainAlias()
        domal.name = "domalias.net"
        domal.target = dom
        domal.save()
        self.assertEqual(dom.domainalias_count, 1)

        domal.name = "domalias.org"
        domal.save()

        domal.delete()

    def test_form(self):
        dom = Domain.objects.get(name="test.com")
        values = dict(name=dom.name, quota=dom.quota, enabled=dom.enabled,
                      aliases="domalias.net", aliases_1="domalias.com")
        self.check_ajax_post(reverse("modoboa.admin.views.editdomain", args=[1]), values)
        self.assertEqual(dom.domainalias_set.count(), 2)

        del values["aliases_1"]
        self.check_ajax_post(reverse("modoboa.admin.views.editdomain", args=[1]), values)
        self.assertEqual(dom.domainalias_set.count(), 1)


class AccountTestCase(ModoTestCase):
    fixtures = ["initial_users.json", "test_content.json",]

    def test_crud(self):
        values = dict(username="tester@test.com", first_name="Tester", last_name="Toto",
                      password1="toto", password2="toto", role="SimpleUsers",
                      quota_act=True,
                      is_active=True, email="tester@test.com", stepid=2)
        self.check_ajax_post(reverse("modoboa.admin.views.newaccount"), values)

        account = User.objects.get(username="tester@test.com")
        mb = account.mailbox_set.all()[0]
        self.assertEqual(mb.full_address, "tester@test.com")
        self.assertEqual(mb.quota, 100)
        self.assertEqual(mb.enabled, True)
        self.assertEqual(mb.quota_value.username, "tester@test.com")
        self.assertEqual(account.username, mb.full_address)
        self.assertTrue(account.check_password("toto"))
        self.assertEqual(account.first_name, "Tester")
        self.assertEqual(account.last_name, "Toto")
        self.assertEqual(mb.domain.mailbox_count, 4)

        values["username"] = "pouet@test.com"
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[account.id]), values)

        mb = Mailbox.objects.get(pk=mb.id)
        self.assertEqual(mb.full_address, "pouet@test.com")

        self.check_ajax_get(reverse("modoboa.admin.views.delaccount", args=[account.id]), {})

    def test_update_password(self):
        """Password update

        Two cases:
        * The default admin changes his password (no associated Mailbox)
        * A normal user changes his password
        """
        self.check_ajax_post(reverse("modoboa.userprefs.views.profile"),
                             {"oldpassword" : "password", 
                              "newpassword" : "titi", "confirmation" : "titi"})
        self.clt.logout()

        self.assertEqual(self.clt.login(username="admin", password="titi"), True)
        self.assertEqual(self.clt.login(username="user@test.com", password="toto"),
                         True)

        self.check_ajax_post(reverse("modoboa.userprefs.views.profile"),
                            {"oldpassword" : "toto", 
                             "newpassword" : "tutu", "confirmation" : "tutu"})
        self.clt.logout()
        self.assertEqual(self.clt.login(username="user@test.com", password="tutu"), True)


class AliasTestCase(ModoTestCase):
    fixtures = ["initial_users.json", "test_content.json"]

    def test_alias(self):
        user = User.objects.get(username="user@test.com")
        values = dict(
            username="user@test.com", role=user.group,
            is_active=user.is_active, email="user@test.com",
            aliases="toto@test.com", aliases_1="titi@test.com"
        )
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[user.id]), values)
        self.assertEqual(user.mailbox_set.all()[0].alias_set.count(), 2)

        del values["aliases_1"]
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[user.id]), values)
        self.assertEqual(user.mailbox_set.all()[0].alias_set.count(), 1)

    def test_dlist(self):
        values = dict(email="all@test.com",
                      recipients="user@test.com",
                      recipients_1="admin@test.com",
                      recipients_2="ext@titi.com",
                      enabled=True)
        self.check_ajax_post(reverse("modoboa.admin.views.newdlist"), values)
        user = User.objects.get(username="user@test.com")
        self.assertEqual(len(user.mailbox_set.all()[0].alias_set.all()), 1)
        admin = User.objects.get(username="admin@test.com")
        self.assertEqual(len(admin.mailbox_set.all()[0].alias_set.all()), 1)

        dlist = Alias.objects.get(address="all", domain__name="test.com")
        self.assertEqual(len(dlist.get_recipients()), 3)
        del values["recipients_1"]
        self.check_ajax_post(reverse("modoboa.admin.views.editalias", args=[dlist.id]),
                             values)
        self.assertEqual(dlist.get_recipients_count(), 2)

        self.check_ajax_get(reverse("modoboa.admin.views.deldlist") + "?selection=%d" \
                                % dlist.id, {})
        self.assertRaises(Alias.DoesNotExist, Alias.objects.get, 
                          address="all", domain__name="test.com")

    def test_forward(self):
        values = dict(email="forward@test.com", recipients="rcpt@dest.com")
        self.check_ajax_post(reverse("modoboa.admin.views.newforward"), values)
        fwd = Alias.objects.get(address="forward", domain__name="test.com")
        self.assertEqual(fwd.get_recipients_count(), 1)

        values["recipients"] = "rcpt2@dest.com"
        self.check_ajax_post(reverse("modoboa.admin.views.editalias", args=[fwd.id]),
                             values)
        self.assertEqual(fwd.get_recipients_count(), 1)

        self.check_ajax_get(reverse("modoboa.admin.views.delforward") + "?selection=%d" \
                                % fwd.id, {})
        self.assertRaises(Alias.DoesNotExist, Alias.objects.get, 
                          address="forward", domain__name="test.com")

    def test_forward_and_local_copies(self):
        values = dict(email="user@test.com", recipients="rcpt@dest.com")
        self.check_ajax_post(reverse("modoboa.admin.views.newforward"), values)
        fwd = Alias.objects.get(address="user", domain__name="test.com")
        self.assertEqual(fwd.get_recipients_count(), 1)

        values["recipients"] = "rcpt@dest.com"
        values["recipients_1"] = "user@test.com"
        self.check_ajax_post(reverse("modoboa.admin.views.editalias", args=[fwd.id]),
                             values)
        fwd = Alias.objects.get(pk=fwd.pk)
        self.assertEqual(fwd.get_recipients_count(), 2)
        self.assertEqual(fwd.aliases.count(), 0)


class PermissionsTestCase(ModoTestCase):
    fixtures = ["initial_users.json", "test_content.json"]

    def setUp(self):
        """
        FIXME: je n'arrive pas à générer des données de test incluant
        déjà les permissions (cf. table ObjectAccess). C'est pour
        cette raison que j'assigne le domaine test.com ici...
        """
        super(PermissionsTestCase, self).setUp()
        self.user = User.objects.get(username="user@test.com")
        self.values = dict(
            username=self.user.username, role="DomainAdmins",
            is_active=self.user.is_active, email="user@test.com"
        )
        self.admin = User.objects.get(username="admin@test.com")
        dom = Domain.objects.get(name="test.com")
        dom.add_admin(self.admin)

    def tearDown(self):
        self.clt.logout()

    def test_domain_admins(self):
        self.values["role"] = "DomainAdmins"
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[self.user.id]),
                             self.values)
        self.assertEqual(self.user.group == "DomainAdmins", True)

        self.values["role"] = "SimpleUsers"
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[self.user.id]),
                             self.values)
        self.assertEqual(self.user.group == 'DomainAdmins', False)

    def test_superusers(self):
        self.values["role"] = "SuperAdmins"
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[self.user.id]),
                             self.values)
        self.assertEqual(User.objects.get(username="user@test.com").is_superuser, True)

        self.values["role"] = "SimpleUsers"
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[self.user.id]),
                             self.values)
        self.assertEqual(User.objects.get(username="user@test.com").is_superuser, False)

    def test_self_modif(self):
        self.clt.logout()
        self.assertEqual(self.clt.login(username="admin@test.com", password="toto"),
                         True)
        admin = User.objects.get(username="admin@test.com")
        values = dict(username="admin@test.com", first_name="Admin", password1="", password2="",
                      quota=10, is_active=True, email="admin@test.com")
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[admin.id]), values)
        self.assertEqual(admin.group, "DomainAdmins")
        self.assertEqual(admin.can_access(Domain.objects.get(name="test.com")), True)

        values["role"] = "SuperAdmins"
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[admin.id]), values)
        admin = User.objects.get(username="admin@test.com")
        self.assertEqual(admin.group, "DomainAdmins")

    def test_domadmin_access(self):
        self.clt.logout()
        self.assertEqual(self.clt.login(username="admin@test.com", password="toto"),
                         True)
        response = self.clt.get(reverse("modoboa.admin.views.domains"))
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username="user@test.com")
        response = self.clt.get(reverse("modoboa.admin.views.editaccount", args=[user.id]),
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotEqual(response["Content-Type"], "application/json")

    def test_domainadmin_deletes_superadmin(self):
        """Check domain admins restrictions about super admins

        When a super admin owns a mailbox and a domain admin exists
        for the associated domain, this domain admin must not be able
        to access the super admin.
        """
        values = dict(username="superadmin2@test.com", first_name="Super", last_name="Admin",
                      password1="toto", password2="toto", role="SuperAdmins",
                      is_active=True, email="superadmin2@test.com", stepid=2)
        self.check_ajax_post(reverse("modoboa.admin.views.newaccount"), values)

        account = User.objects.get(username="superadmin2@test.com")
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        self.check_ajax_get(reverse("modoboa.admin.views.delaccount", args=[account.id]), {},
                            status="ko", respmsg="Permission denied")
        self.check_ajax_get(reverse("modoboa.admin.views.delaccount", args=[account.id]), {},
                            status="ko", respmsg="Permission denied")


class ImportTestCase(ModoTestCase):
    fixtures = ["initial_users.json", "test_content.json"]

    def setUp(self):
        super(ImportTestCase, self).setUp()
        self.admin = User.objects.get(username="admin@test.com")
        dom = Domain.objects.get(name="test.com")
        dom.add_admin(self.admin)

    def test_domains_import(self):
        f = ContentFile(b"""domain; domain1.com; 100; True
domain; domain2.com; 200; False
domainalias; domalias1.com; domain1.com; True
""", name="domains.csv")
        self.clt.post(reverse("modoboa.admin.views.import_domains"), {
            "sourcefile": f
        })
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
        self.clt.post(reverse("modoboa.admin.views.import_identities"), {
            "sourcefile": f, "crypt_password": True
        })
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
        self.clt.post(reverse("modoboa.admin.views.import_identities"), {
            "sourcefile": f, "crypt_password": True, "continue_if_exists": True
        })

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
        self.clt.post(reverse("modoboa.admin.views.import_identities"), {
            "sourcefile": f, "crypt_password": True, "continue_if_exists": True
        })
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="sa@test.com")

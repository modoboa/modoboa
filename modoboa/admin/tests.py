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
from models import *
from modoboa.admin.lib import *
from modoboa.lib import parameters
from modoboa.lib.tests import ModoTestCase


class DomainTestCase(TestCase):
    fixtures = ["initial_users.json"]

    def test(self):
        dom = Domain.objects.create(name="test.com", quota=100)
        self.assertIsNotNone(dom)
        self.assertEqual(dom.name, "test.com")
        self.assertEqual(dom.quota, 100)
        self.assertEqual(dom.enabled, False)

        dom.name = "toto.com"
        dom.save()
        self.assertEqual(dom.name, "toto.com")

        dom.delete(User.objects.get(pk=1))


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
        clt = Client()
        clt.login(username="admin", password="password")
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

    def setUp(self):
        super(AccountTestCase, self).setUp()
        from modoboa import admin

    def test(self):
        values = dict(username="tester@test.com", first_name="Tester", last_name="Toto",
                      password1="toto", password2="toto", role="SimpleUsers",
                      is_active=True, email="tester@test.com", stepid=2)
        self.check_ajax_post(reverse("modoboa.admin.views.newaccount"), values)

        account = User.objects.get(username="tester@test.com")
        mb = account.mailbox_set.all()[0]
        self.assertEqual(mb.full_address, "tester@test.com")
        self.assertEqual(mb.quota, 100)
        self.assertEqual(mb.enabled, True)
        self.assertEqual(account.username, mb.full_address)
        self.assertTrue(account.check_password("toto"))
        self.assertEqual(account.first_name, "Tester")
        self.assertEqual(account.last_name, "Toto")
        self.assertEqual(mb.domain.mailbox_count, 4)

        values["email"] = "pouet@test.com"
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[account.id]), values)

        mb = Mailbox.objects.get(pk=mb.id)
        self.assertEqual(mb.full_address, "pouet@test.com")

        self.check_ajax_get(reverse("modoboa.admin.views.delaccount") + "?selection=%d" \
                                % account.id, {})

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
            username="user@test.com", role="SimpleUsers", 
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
        self.check_ajax_post(reverse("modoboa.admin.views.editalias_dispatcher", args=[dlist.id]),
                             values)
        self.assertEqual(dlist.get_recipients_count(), 2)
        
        self.check_ajax_get(reverse("modoboa.admin.views.deldlist") + "?selection=%d" \
                                % dlist.id, {})
        self.assertRaises(Alias.DoesNotExist, Alias.objects.get, 
                          address="all", domain__name="test.com")

    def test_forward(self):
        values = dict(email="forward@test.com", ext_recipient="rcpt@dest.com")
        self.check_ajax_post(reverse("modoboa.admin.views.newforward"), values)
        fwd = Alias.objects.get(address="forward", domain__name="test.com")
        self.assertEqual(len(fwd.get_recipients()), 1)
        
        values["recipient"] = "rcpt2@dest.com"
        self.check_ajax_post(reverse("modoboa.admin.views.editalias_dispatcher", args=[fwd.id]),
                             values)
        self.assertEqual(fwd.get_recipients_count(), 1)
        
        self.check_ajax_get(reverse("modoboa.admin.views.delforward") + "?selection=%d" \
                                % fwd.id, {})
        self.assertRaises(Alias.DoesNotExist, Alias.objects.get, 
                          address="forward", domain__name="test.com")


class PermissionsTestCase(ModoTestCase):
    fixtures = ["initial_users.json", "test_content.json"]

    def setUp(self):
        """
        FIXME: je n'arrive pas à générer des données de test incluant
        déjà les permissions (cf. table ObjectAccess). C'est pour
        cette raison que j'assigne le domaine test.com ici...
        """
        from modoboa.lib.permissions import grant_access_to_object

        super(PermissionsTestCase, self).setUp()
        self.user = User.objects.get(username="user@test.com")
        self.values = dict(
            username=self.user.username, role="DomainAdmins", 
            is_active=self.user.is_active, email="user@test.com"
            )
        self.admin = User.objects.get(username="admin@test.com")
        self.check_ajax_post(reverse("modoboa.admin.views.editaccount", args=[self.admin.id]), dict(
                username=self.admin.username, role="DomainAdmins", 
                is_active=self.admin.is_active, email="admin@test.com",
                password1="", password2="", domains="test.com"
                ))

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
                      is_active=True, email="admin@test.com")
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
                      is_active=True, email="superadmin@test.com", stepid=2)
        self.check_ajax_post(reverse("modoboa.admin.views.newaccount"), values)
        
        account = User.objects.get(username="superadmin2@test.com")
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        self.check_ajax_get(reverse("modoboa.admin.views.delaccount") + "?selection=%d" \
                                % account.id, {},
                            status="ko", respmsg="Permission denied")
        self.check_ajax_get(reverse("modoboa.admin.views.delaccount") + "?selection=%d" \
                                % 4, {},
                            status="ko", respmsg="Permission denied")
        

from django.test import TestCase
from django.test.client import Client
from django.utils import simplejson
from models import *
from modoboa.admin.lib import *
from modoboa.lib import parameters

import os

class DomainTestCase(TestCase):

    def test(self):
        dom = Domain.objects.create(name="test.com", quota=100)
        self.assertIsNotNone(dom)
        self.assertEqual(dom.name, "test.com")
        self.assertEqual(dom.quota, 100)
        self.assertEqual(dom.enabled, False)

        self.assertEqual(dom.create_dir(), True)
        path = os.path.join(parameters.get_admin("STORAGE_PATH"), dom.name)
        self.assertEqual(os.path.exists(path), True)
        
        dom.name = "toto.com"
        dom.save()
        self.assertEqual(dom.name, "toto.com")
        path = os.path.join(parameters.get_admin("STORAGE_PATH"), dom.name)
        self.assertEqual(os.path.exists(path), True)

        dom.delete()
        self.assertEqual(os.path.exists(path), False)

class DomainAliasTestCase(TestCase):
    fixtures = ["test_content.json"]
    
    def test(self):
        dom = Domain.objects.get(name="test.com")
        domal = DomainAlias()
        domal.name = "domalias.net"
        domal.target = dom
        domal.save()
        self.assertEqual(dom.domainalias_count, 1)

        domal.name = "domalias.org"
        domal.save()

        domal.delete()
        

class MailboxTestCase(TestCase):
    fixtures = ["test_content.json",]

    def test(self):
        dom = Domain.objects.get(name="test.com")
        mb = Mailbox()
        mb.address = "tester"
        mb.domain = dom
        mb.save(name="Tester toto", password="toto", enabled=True)
        self.assertEqual(mb.full_address, "tester@test.com")
        self.assertEqual(os.path.exists(mb.full_path), True)
        self.assertEqual(mb.quota, 100)
        self.assertEqual(mb.enabled, True)
        self.assertIsNotNone(mb.user)
        self.assertEqual(mb.user.username, mb.full_address)
        self.assertTrue(mb.user.check_password("toto"))
        self.assertEqual(mb.user.first_name, "Tester")
        self.assertEqual(mb.user.last_name, "toto")
        self.assertEqual(dom.mailbox_count, 2)

        mb.address = "pouet"
        mb.save()
        self.assertEqual(mb.path, "%s/" % mb.address)
        path = mb.full_path
        self.assertEqual(mb.full_address, "pouet@test.com")
        self.assertEqual(os.path.exists(path), True)

        mb.delete()
        self.assertEqual(os.path.exists(path), False)

    def test_update_password(self):
        """Password update

        Two cases:
        * The default admin changes his password (no associated Mailbox)
        * A normal user changes his password
        """
        clt = Client()
        self.assertEqual(clt.login(username="admin", password="password"), True)
        response = clt.post("/modoboa/userprefs/changepassword/",
                            {"oldpassword" : "password", 
                             "newpassword" : "titi", "confirmation" : "titi"})
        self.assertEqual(response.status_code, 200)
        obj = simplejson.loads(response.content)
        self.assertEqual(obj["status"], "ok")
        clt.logout()
        self.assertEqual(clt.login(username="admin", password="titi"), True)

        self.assertEqual(clt.login(username="user@test.com", password="toto"),
                         True)
        response = clt.post("/modoboa/userprefs/changepassword/",
                            {"oldpassword" : "toto", 
                             "newpassword" : "tutu", "confirmation" : "tutu"})
        self.assertEqual(response.status_code, 200)
        obj = simplejson.loads(response.content)
        self.assertEqual(obj["status"], "ok")
        clt.logout()
        self.assertEqual(clt.login(username="user@test.com", password="tutu"), True)
        
       
class AliasTestCase(TestCase):
    fixtures = ["test_content.json"]
    
    def test(self):
        dom = Domain.objects.get(name="test.com")
        mb = Mailbox.objects.get(domain=dom, address="user")
        al = Alias()
        al.address = "alias"
        al.domain = dom
        al.enabled = True
        al.save([mb], ["toto@extdomain.com"])
        self.assertEqual(al.full_address, "alias@test.com")
        self.assertEqual(mb.alias_count, 1)

        al.address = "global"
        al.save([mb], [])
        self.assertEqual(al.full_address, "global@test.com")
        self.assertEqual(mb.alias_count, 1)
        self.assertEqual(al.extmboxes, "")

        al.delete()
        self.assertEqual(mb.alias_count, 0)

class PermissionsTestCase(TestCase):
    fixtures = ["test_content.json"]

    def setUp(self):
        self.clt = Client()
        self.clt.login(username="admin", password="password")
        self.user = User.objects.get(username="user@test.com")
        
    def tearDown(self):
        self.clt.logout()

    def test_domain_admins(self):
        response = self.clt.post("/modoboa/admin/permissions/domainadmin/promote/",
                                 {"name" : self.user.username})
        self.assertEqual(response.status_code, 200)
        obj = simplejson.loads(response.content)
        self.assertEqual(obj["status"], "ok")
        self.assertEqual(self.user.belongs_to_group('DomainAdmins'), True)

        response = self.clt.get("/modoboa/admin/permissions/delete/",
                                {"role" : "domain_admins", 
                                 "selection" : self.user.id})
        self.assertEqual(response.status_code, 200)
        obj = simplejson.loads(response.content)
        self.assertEqual(obj["status"], "ok")
        self.assertEqual(self.user.belongs_to_group('DomainAdmins'), False)

    def test_superusers(self):
        response = self.clt.post("/modoboa/admin/permissions/add/",
                                 {"role" : "super_admins", "user" : self.user.id})
        self.assertEqual(response.status_code, 200)
        obj = simplejson.loads(response.content)
        self.assertEqual(obj["status"], "ok")
        self.assertEqual(User.objects.get(username="user@test.com").is_superuser, True)

        response = self.clt.get("/modoboa/admin/permissions/delete/",
                                {"role" : "super_admins", "selection" : self.user.id})
        self.assertEqual(response.status_code, 200)
        obj = simplejson.loads(response.content)
        self.assertEqual(obj["status"], "ok")
        self.assertEqual(User.objects.get(username="user@test.com").is_superuser, False)


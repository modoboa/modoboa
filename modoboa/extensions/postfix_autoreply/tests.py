from django.core.urlresolvers import reverse
from modoboa.core.models import User
from modoboa.lib.tests import ExtTestCase
from modoboa.extensions.admin import factories
from modoboa.extensions.admin.models import (
    Domain
)
from modoboa.extensions.postfix_autoreply.models import (
    Transport, Alias, ARmessage
)


class EventsTestCase(ExtTestCase):
    fixtures = ['initial_users.json']

    def setUp(self):
        super(EventsTestCase, self).setUp()
        self.activate_extensions('postfix_autoreply')
        factories.populate_database()

    def test_domain_created_event(self):
        values = {
            "name": "domain.tld", "quota": 100, "create_dom_admin": "no",
            "stepid": 'step2'
        }
        self.ajax_post(
            reverse("admin:domain_add"), values
        )
        trans = Transport.objects.get(domain='autoreply.domain.tld')

    def test_domain_deleted_event(self):
        dom = Domain.objects.get(name="test.com")
        trans = Transport.objects.get(domain='autoreply.test.com')
        self.ajax_post(
            reverse("admin:domain_delete", args=[dom.id]),
            {}
        )
        with self.assertRaises(Transport.DoesNotExist):
            Transport.objects.get(domain='autoreply.test.com')

    def test_domain_modified_event(self):
        values = {
            "name": "test.fr", "quota": 100, "enabled": True
        }
        dom = Domain.objects.get(name="test.com")
        self.ajax_post(
            reverse("admin:domain_change", args=[dom.id]),
            values
        )
        trans = Transport.objects.get(domain='autoreply.test.fr')
        self.assertEqual(
            Alias.objects.filter(full_address__contains='@test.fr').count(), 2
        )
        for al in Alias.objects.filter(full_address__contains='@test.fr'):
            self.assertIn('autoreply.test.fr', al.autoreply_address)

    def test_mailbox_created_event(self):
        values = {
            'username': "tester@test.com",
            'first_name': 'Tester', 'last_name': 'Toto',
            'password1': 'toto', 'password2': 'toto', 'role': 'SimpleUsers',
            'quota_act': True, 'is_active': True, 'email': 'tester@test.com',
            'stepid': 'step2', 'autoreply': 'no'
        }
        self.ajax_post(
            reverse("admin:account_add"), values
        )
        al = Alias.objects.get(full_address='tester@test.com')
        self.assertEqual(
            al.autoreply_address, 'tester@test.com@autoreply.test.com')
        arm = ARmessage.objects.get(mbox__address='tester')

    def test_mailbox_deleted_event(self):
        account = User.objects.get(username="user@test.com")
        self.ajax_post(
            reverse("admin:account_delete", args=[account.id]),
            {}
        )
        with self.assertRaises(Alias.DoesNotExist):
            Alias.objects.get(full_address='user@test.com')
        with self.assertRaises(ARmessage.DoesNotExist):
            ARmessage.objects.get(
                mbox__address='user', mbox__domain__name='test.com')


    def test_modify_mailbox_event(self):
        values = {
            'username': "leon@test.com",
            'first_name': 'Tester', 'last_name': 'Toto',
            'role': 'SimpleUsers', 'quota_act': True,
            'is_active': True, 'email': 'leon@test.com',
            'autoreply': 'no'
        }
        account = User.objects.get(username="user@test.com")
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]),
            values
        )
        with self.assertRaises(Alias.DoesNotExist):
            Alias.objects.get(full_address='user@test.com')
        al = Alias.objects.get(full_address='leon@test.com')


class FormTestCase(ExtTestCase):
    fixtures = ['initial_users.json']

    def setUp(self):
        super(FormTestCase, self).setUp()
        self.activate_extensions('postfix_autoreply')
        factories.populate_database()

    # def test_set_autoreply(self):
    #     self.clt.get(
    #         reverse('modoboa.core.views.user.index')
    #     )
    #     values = {
    #         'subject': 'test', 'content': "I'm off", "enabled": True
    #     }
    #     self.ajax_post(
    #         reverse('modoboa.extensions.postfix_autoreply.views.autoreply'),
    #         values
    #     )
    #     account = User.objects.get(username="user@test.com")
    #     arm = ARmessage.objects.get(mbox=account.mailbox_set.all()[0])
    #     self.assertEqual(arm.subject, 'test')
    #     self.assertTrue(arm.enabled)
    #     self.assertFalse(arm.untildate)
    #     self.assertTrue(arm.fromdate)

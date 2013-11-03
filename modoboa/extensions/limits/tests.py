from django.core.urlresolvers import reverse
from modoboa.lib.tests import ExtTestCase
from modoboa.core.factories import UserFactory
from modoboa.extensions.admin.factories import DomainFactory, MailboxFactory
from modoboa.core.models import User


class PermissionsTestCase(ExtTestCase):
    fixtures = ["initial_users.json"]
    name = "limits"

    def setUp(self):
        super(PermissionsTestCase, self).setUp()
        dom = DomainFactory(name='test.com')
        self.admin = UserFactory(
            username='admin@test.com', groups=('DomainAdmins',)
        )
        MailboxFactory(address='admin', domain=dom, user=self.admin)
        dom.add_admin(self.admin)

    def test_domainadmin_deletes_reseller(self):
        """Check if a domain admin can delete a reseller.

        Expected result: no.
        """
        values = dict(
            username="reseller@test.com", first_name="Reseller", last_name="",
            password1="toto", password2="toto", role="Resellers",
            is_active=True, email="reseller@test.com", stepid=2
        )
        self.check_ajax_post(reverse("modoboa.extensions.admin.views.identity.newaccount"), values)
        account = User.objects.get(username="reseller@test.com")
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        self.check_ajax_get(
            reverse("modoboa.extensions.admin.views.identity.delaccount", args=[account.id]),
            {}, status="ko", respmsg="Permission denied"
        )

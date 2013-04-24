from django.core.urlresolvers import reverse
from modoboa.lib.tests import ExtTestCase
from modoboa.admin.models import User


class PermissionsTestCase(ExtTestCase):
    fixtures = ["initial_users.json", "test_content.json"]
    name = "limits"

    def test_domainadmin_deletes_reseller(self):
        """Check if a domain admin can delete a reseller.

        Expected result: no.
        """
        values = dict(
            username="reseller@test.com", first_name="Reseller", last_name="",
            password1="toto", password2="toto", role="Resellers",
            is_active=True, email="reseller@test.com", stepid=2
        )
        self.check_ajax_post(reverse("modoboa.admin.views.newaccount"), values)
        account = User.objects.get(username="reseller@test.com")
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        self.check_ajax_get(reverse("modoboa.admin.views.delaccount") + "?selection=%d" \
                                % account.id, {},
                            status="ko", respmsg="Permission denied")
        self.check_ajax_get(reverse("modoboa.admin.views.delaccount") + "?selection=%d" \
                                % 4, {},
                            status="ko", respmsg="Permission denied")

        

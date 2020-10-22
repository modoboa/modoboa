"""User related tests."""

from django.urls import reverse

from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from ..factories import populate_database
from ..models import Alias


class ForwardTestCase(ModoTestCase):
    """User forward test cases."""

    def setUp(self):
        super(ForwardTestCase, self).setUp()
        populate_database()

    def test_set_forward(self):
        self.client.logout()
        self.client.login(username="user@test.com", password="toto")
        url = reverse("user_forward")
        self.ajax_post(
            url,
            {"dest": "user@extdomain.com", "keepcopies": True}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("user@extdomain.com", content["content"])
        self.assertNotIn("user@test.com", content["content"])
        forward = Alias.objects.get(address="user@test.com", internal=False)
        sadmin = User.objects.get(username="admin")
        self.assertTrue(sadmin.can_access(forward))
        domadmin = User.objects.get(username="admin@test.com")
        self.assertTrue(domadmin.can_access(forward))

        selfalias = Alias.objects.get(address="user@test.com", internal=True)
        self.assertTrue(selfalias.enabled)

        # Deactivate local copies
        self.ajax_post(
            url,
            {"dest": "user@extdomain.com", "keepcopies": False}
        )
        selfalias.refresh_from_db()
        self.assertFalse(selfalias.enabled)

        # Now, empty forward
        self.ajax_post(url, {"dest": "", "keepcopies": False})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertNotIn("user@extdomain.com", content["content"])
        selfalias.refresh_from_db()
        self.assertTrue(selfalias.enabled)

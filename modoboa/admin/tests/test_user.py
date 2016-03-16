from django.core.urlresolvers import reverse

from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase

from ..factories import populate_database
from ..models import Alias


class ForwardTestCase(ModoTestCase):

    def setUp(self):
        super(ForwardTestCase, self).setUp()
        populate_database()

    def test_forward_permissions(self):
        self.client.logout()
        self.client.login(username='user@test.com', password='toto')
        self.ajax_post(
            reverse('user_forward'),
            {'dest': 'user@extdomain.com', 'keepcopies': True}
        )
        forward = Alias.objects.get(address='user@test.com', internal=False)
        sadmin = User.objects.get(username='admin')
        self.assertTrue(sadmin.can_access(forward))
        domadmin = User.objects.get(username='admin@test.com')
        self.assertTrue(domadmin.can_access(forward))

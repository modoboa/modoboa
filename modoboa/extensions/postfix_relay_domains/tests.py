from modoboa.lib.tests import ExtTestCase
from modoboa.extensions.admin import factories


class RelayDomainsTestCase(ExtTestCase):
    fixtures = ["initial_users.json"]
    name = "postfix_relay_domains"

    def setUp(self):
        super(RelayDomainsTestCase, self).setUp()
        factories.populate_database()

    

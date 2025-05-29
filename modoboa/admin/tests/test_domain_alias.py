from modoboa.lib.tests import ModoTestCase
from .. import factories
from ..models import Alias, Domain, DomainAlias


class DomainAliasTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()
        cls.dom = Domain.objects.get(name="test.com")

    def test_model(self):
        dom = Domain.objects.get(name="test.com")
        domal = DomainAlias()
        domal.name = "domalias.net"
        domal.target = dom
        domal.save()
        self.assertEqual(dom.domainalias_count, 1)
        self.assertTrue(Alias.objects.filter(address=f"@{domal.name}").exists())

        domal.name = "domalias.org"
        domal.save()

        domal.delete()
        self.assertFalse(Alias.objects.filter(address=f"@{domal.name}").exists())

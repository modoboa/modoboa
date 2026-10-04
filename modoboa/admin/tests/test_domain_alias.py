from modoboa.lib.tests import ModoTestCase
from .. import factories
from ..models import Alias, AliasRecipient, Domain, DomainAlias


class DomainAliasTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()
        cls.dom = Domain.objects.get(name="test.com")

    def _get_recipients(self, address):
        alias = Alias.objects.get(address=address, internal=True, domain__isnull=True)
        return list(alias.aliasrecipient_set.values_list("address", flat=True))

    def test_model(self):
        dom = Domain.objects.get(name="test.com")
        domal = DomainAlias()
        domal.name = "domalias.net"
        domal.target = dom
        domal.save()
        self.assertEqual(dom.domainalias_count, 1)
        self.assertEqual(self._get_recipients("@domalias.net"), ["@test.com"])

        domal.name = "domalias.org"
        domal.save()
        self.assertFalse(Alias.objects.filter(address="@domalias.net").exists())
        self.assertEqual(self._get_recipients("@domalias.org"), ["@test.com"])

        domal.target = Domain.objects.get(name="test2.com")
        domal.save()
        self.assertEqual(self._get_recipients("@domalias.org"), ["@test2.com"])

        domal.delete()
        self.assertFalse(Alias.objects.filter(address="@domalias.org").exists())

    def test_rename_over_stale_alias(self):
        """Check a stale generated alias does not prevent a rename."""
        stale = Alias.objects.create(address="@stale.net", internal=True)
        AliasRecipient.objects.create(address="@test2.com", alias=stale)
        domal = factories.DomainAliasFactory(name="domalias.net", target=self.dom)
        domal.name = "stale.net"
        domal.save()
        self.assertEqual(self._get_recipients("@stale.net"), ["@test.com"])

    def test_delete_keeps_domain_aliases(self):
        """Check deletion only removes the generated alias.

        Covers installations where a domain alias already collides
        with a domain.
        """
        victim = Domain.objects.get(name="test2.com")
        catchall = factories.AliasFactory(address="@test2.com", domain=victim)
        factories.AliasRecipientFactory(address="user@external.com", alias=catchall)
        domal = factories.DomainAliasFactory(name="parked.example", target=self.dom)
        domal.name = "test2.com"
        domal.save()
        self.assertTrue(
            Alias.objects.filter(address="@test2.com", internal=True).exists()
        )
        domal.delete()
        self.assertFalse(
            Alias.objects.filter(address="@test2.com", internal=True).exists()
        )
        self.assertTrue(Alias.objects.filter(pk=catchall.pk).exists())
        self.assertEqual(catchall.aliasrecipient_set.count(), 1)

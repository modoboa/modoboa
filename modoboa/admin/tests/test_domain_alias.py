from modoboa.lib.exceptions import Conflict
from modoboa.lib.tests import ModoTestCase
from .. import factories
from ..checks import check_domain_namespace
from ..handlers import get_domainalias_internal_aliases
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

    def _create_legacy_collision(self, direct_create=False):
        """Simulate a collision created by a previous version.

        Signal handlers are bypassed, like the old rename path did. With
        direct_create, the generated alias is stored under the
        colliding name.
        """
        domal = factories.DomainAliasFactory(name="parked.example", target=self.dom)
        DomainAlias.objects.filter(pk=domal.pk).update(name="test2.com")
        if direct_create:
            get_domainalias_internal_aliases("parked.example").update(
                address="@test2.com"
            )
        return DomainAlias.objects.get(pk=domal.pk)

    def test_name_conflict(self):
        """Check domains and domain aliases share the same namespace."""
        with self.assertRaises(Conflict):
            DomainAlias(name="test2.com", target=self.dom).save()
        domal = factories.DomainAliasFactory(name="domalias.net", target=self.dom)
        domal.name = "test2.com"
        with self.assertRaises(Conflict):
            domal.save()
        with self.assertRaises(Conflict):
            Domain(name="domalias.net", quota=0, default_mailbox_quota=0).save()
        dom = Domain.objects.get(name="test2.com")
        dom.name = "domalias.net"
        with self.assertRaises(Conflict):
            dom.save()

    def test_legacy_collision_target_update(self):
        """Check a target change does not make a domain an alias."""
        domal = self._create_legacy_collision()
        domal.target = factories.DomainFactory(name="new.example")
        domal.save()
        self.assertFalse(Alias.objects.filter(address="@test2.com").exists())
        self.assertEqual(self._get_recipients("@parked.example"), ["@test.com"])

    def test_delete_keeps_domain_aliases(self):
        """Check deletion only removes the generated alias."""
        victim = Domain.objects.get(name="test2.com")
        catchall = factories.AliasFactory(address="@test2.com", domain=victim)
        factories.AliasRecipientFactory(address="user@external.com", alias=catchall)
        domal = self._create_legacy_collision(direct_create=True)
        self.assertTrue(
            Alias.objects.filter(address="@test2.com", internal=True).exists()
        )
        domal.delete()
        self.assertFalse(
            Alias.objects.filter(address="@test2.com", internal=True).exists()
        )
        self.assertTrue(Alias.objects.filter(pk=catchall.pk).exists())
        self.assertEqual(catchall.aliasrecipient_set.count(), 1)

    def test_namespace_check(self):
        """Check legacy inconsistencies are reported."""
        factories.DomainAliasFactory(name="domalias.net", target=self.dom)
        self.assertEqual(check_domain_namespace(None, databases=["default"]), [])
        self._create_legacy_collision()
        msgs = check_domain_namespace(None, databases=["default"])
        self.assertEqual(
            [msg.id for msg in msgs], ["modoboa.admin.W001", "modoboa.admin.W002"]
        )
        self.assertIn("test2.com", msgs[0].msg)
        self.assertIn("@parked.example", msgs[1].msg)

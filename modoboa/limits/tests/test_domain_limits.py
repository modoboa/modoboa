# coding: utf-8
"""Test cases for the limits extension."""

from django.core.urlresolvers import reverse

from modoboa.admin.factories import populate_database
from modoboa.admin.models import Domain
from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib import tests as lib_tests

from .. import utils


class DomainLimitsTestCase(lib_tests.ModoTestCase):
    """Per-domain limits tests."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(DomainLimitsTestCase, cls).setUpTestData()
        parameters.save_admin("ENABLE_DOMAIN_LIMITS", "yes")
        for name, tpl in utils.get_domain_limit_templates():
            parameters.save_admin(
                "DEFLT_DOMAIN_{}_LIMIT".format(name.upper()), 2)
        populate_database()

    def test_set_limits(self):
        """Try to set limits for a given domain."""
        domain = Domain.objects.get(name="test.com")
        values = {
            "name": domain.name, "quota": domain.quota,
            "enabled": domain.enabled, "type": "domain",
            "mailboxes_limit": 3, "mailbox_aliases_limit": 3,
            "domain_aliases_limit": 3
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[domain.id]),
            values
        )
        domain.refresh_from_db()
        self.assertEqual(
            domain.domainobjectlimit_set.get(name="mailboxes").max_value, 3)
        self.assertEqual(
            domain.domainobjectlimit_set.get(
                name="mailbox_aliases").max_value, 3)
        self.assertEqual(
            domain.domainobjectlimit_set.get(
                name="domain_aliases").max_value, 3)

    def test_domain_aliases_limit(self):
        """Try to exceed defined limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="domain_aliases")
        self.assertFalse(limit.is_exceeded())
        values = {
            "name": domain.name, "quota": domain.quota,
            "enabled": domain.enabled, "type": "domain",
            "mailboxes_limit": 2, "mailbox_aliases_limit": 2,
            "domain_aliases_limit": 2,
            "aliases": "alias1.com", "aliases_1": "alias2.com"
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[domain.id]),
            values
        )
        self.assertTrue(limit.is_exceeded())
        values["aliases_2"] = "alias3.com"
        self.ajax_post(
            reverse("admin:domain_change", args=[domain.id]),
            values, 403
        )

    def test_mailboxes_limit(self):
        """Try to exceed defined limits."""
        domain = Domain.objects.get(name="test.com")
        domain.domainobjectlimit_set.filter(name="mailboxes").update(
            max_value=3)
        limit = domain.domainobjectlimit_set.get(name="mailboxes")
        self.assertFalse(limit.is_exceeded())
        username = "toto@test.com"
        values = {
            "username": username,
            "first_name": "Tester", "last_name": "Toto",
            "password1": "Toto1234", "password2": "Toto1234",
            "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": username, "stepid": "step2",
        }
        self.ajax_post(reverse("admin:account_add"), values, 200)
        self.assertTrue(limit.is_exceeded())

        username = "titi@test.com"
        self.ajax_post(reverse("admin:account_add"), values, 400)

    def test_mailbox_aliases_limit(self):
        """Try to exceed defined limits."""
        domain = Domain.objects.get(name="test.com")
        user = User.objects.get(username="user@test.com")
        limit = domain.domainobjectlimit_set.get(name="mailbox_aliases")
        limit.max_value = 4
        limit.save()
        self.assertFalse(limit.is_exceeded())
        values = {
            "username": user.username, "role": user.group,
            "is_active": user.is_active, "email": user.email,
            "quota_act": True,
            "aliases": "alias@test.com", "aliases_1": "alias1@test.com"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self.assertTrue(limit.is_exceeded())

        values["aliases_2"] = "alias2@test.com"
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values, 403
        )

        limit.max_value = 5
        limit.save()
        values = {
            "address": "forward2@test.com", "recipients": "user@test.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        self.assertTrue(limit.is_exceeded())

        values["address"] = "forward3@test.com"
        self.ajax_post(reverse("admin:alias_add"), values, 400)

# -*- coding: utf-8 -*-

"""Test cases for the limits extension."""

from __future__ import unicode_literals

from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.admin.models import Domain
from modoboa.core import factories as core_factories
from modoboa.core.models import User
from modoboa.lib import tests as lib_tests
from .. import utils


class DomainLimitsTestCase(lib_tests.ModoTestCase):
    """Per-domain limits tests."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(DomainLimitsTestCase, cls).setUpTestData()
        cls.localconfig.parameters.set_values({
            "enable_admin_limits": False,
            "enable_domain_limits": True
        })
        for name, _definition in utils.get_domain_limit_templates():
            cls.localconfig.parameters.set_value(
                "deflt_domain_{0}_limit".format(name), 2)
        cls.localconfig.save()
        admin_factories.populate_database()

    def test_set_limits(self):
        """Try to set limits for a given domain."""
        domain = Domain.objects.get(name="test.com")
        values = {
            "name": domain.name, "quota": domain.quota,
            "default_mailbox_quota": domain.default_mailbox_quota,
            "enabled": domain.enabled, "type": "domain",
            "mailboxes_limit": 3, "mailbox_aliases_limit": 3,
            "domain_aliases_limit": 3, "domain_admins_limit": 3
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
        self.assertEqual(
            domain.domainobjectlimit_set.get(
                name="domain_admins").max_value, 3)

    def test_domain_aliases_limit(self):
        """Try to exceed defined limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="domain_aliases")
        self.assertFalse(limit.is_exceeded())
        values = {
            "name": domain.name, "quota": domain.quota,
            "default_mailbox_quota": domain.default_mailbox_quota,
            "enabled": domain.enabled, "type": "domain",
            "mailboxes_limit": 2, "mailbox_aliases_limit": 2,
            "domain_aliases_limit": 2, "domain_admins_limit": 2,
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

    def test_domain_admins_limit(self):
        """Try to exceed defined limit."""
        domain = Domain.objects.get(name="test.com")
        limit = domain.domainobjectlimit_set.get(name="domain_admins")
        self.assertFalse(limit.is_exceeded())
        user = User.objects.get(username="admin@test2.com")
        values = {
            "username": user.username, "role": user.role,
            "is_active": user.is_active, "email": user.email,
            "quota_act": True, "domains": "test2.com",
            "domains_1": "test.com", "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self.assertTrue(limit.is_exceeded())
        user = core_factories.UserFactory(
            username="admin1000@test.com", groups=("DomainAdmins", ))
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values, 400
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
            "username": "toto@test.com",
            "first_name": "Tester", "last_name": "Toto",
            "password1": "Toto1234", "password2": "Toto1234",
            "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": username, "stepid": "step2",
        }
        self.ajax_post(reverse("admin:account_add"), values, 200)
        self.assertTrue(limit.is_exceeded())

        values["username"] = "titi@test.com"
        values["email"] = "titi@test.com"
        self.ajax_post(reverse("admin:account_add"), values, 400)

        # Set unlimited value
        limit.max_value = -1
        limit.save(update_fields=["max_value"])
        self.ajax_post(reverse("admin:account_add"), values)
        self.assertFalse(limit.is_exceeded())

    def test_mailbox_aliases_limit(self):
        """Try to exceed defined limits."""
        domain = Domain.objects.get(name="test.com")
        user = User.objects.get(username="user@test.com")
        limit = domain.domainobjectlimit_set.get(name="mailbox_aliases")
        limit.max_value = 4
        limit.save()
        self.assertFalse(limit.is_exceeded())
        values = {
            "username": user.username, "role": user.role,
            "is_active": user.is_active, "email": user.email,
            "quota_act": True,
            "aliases": "alias@test.com", "aliases_1": "alias1@test.com",
            "language": "en"
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

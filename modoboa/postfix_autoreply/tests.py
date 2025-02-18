"""modoboa-postfix-autoreply unit tests."""

import datetime
from io import StringIO
import sys

from dateutil.relativedelta import relativedelta

from django.core import mail, management
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from modoboa.transport import models as tr_models

from . import factories, models

SIMPLE_EMAIL_CONTENT = """
From: Homer Simpson <homer@simpson.test>
Date: Wed, 15 Mar 2017 18:35:19 +0100
Message-ID: <CAN0378wA1V0VJg5OxyavB2uJgAimMc2ttGSc-yvWsXTaKqnKuw@simpson.test>
Subject: Test
To: user@test.com
Content-Type: multipart/alternative; boundary=001a114420be4c231a054ac85e75

--001a114420be4c231a054ac85e75
Content-Type: text/plain; charset=UTF-8

pouet

--001a114420be4c231a054ac85e75
Content-Type: text/html; charset=UTF-8

<div dir="ltr">pouet<br></div>

--001a114420be4c231a054ac85e75--
"""

SIMPLE_EMAIL_CONTENT_WITH_BAD_HEADER = """
From: Homer Simpson <homer@simpson.test>
Date: Wed, 15 Mar 2017 18:35:19 +0100
Message-ID:
 <CAN0378wA1V0VJg5OxyavB2uJgAimMc2ttGSc-yvWsXTaKqnKuw@simpson.test>
Subject: Test
To: user@test.com
Content-Type: multipart/alternative; boundary=001a114420be4c231a054ac85e75

--001a114420be4c231a054ac85e75
Content-Type: text/plain; charset=UTF-8

pouet

--001a114420be4c231a054ac85e75
Content-Type: text/html; charset=UTF-8

<div dir="ltr">pouet<br></div>

--001a114420be4c231a054ac85e75--
"""

ENCODED_EMAIL_SUBJECT = r"""
From: Homer Simpson <homer@simpson.test>
Date: Wed, 15 Mar 2017 18:35:19 +0100
Message-ID: <CAN0378wA1V0VJg5OxyavB2uJgAimMc2ttGSc-yvWsXTaKqnKuw@simpson.test>
Subject: =?utf-8?q?A_m=C3=A9_non!!?=\n =?utf-8?q?_=C3=A7a_va_pas!!?=
To: user@test.com
Content-Type: multipart/alternative; boundary=001a114420be4c231a054ac85e75

--001a114420be4c231a054ac85e75
Content-Type: text/plain; charset=UTF-8

pouet

--001a114420be4c231a054ac85e75
Content-Type: text/html; charset=UTF-8

<div dir="ltr">pouet<br></div>

--001a114420be4c231a054ac85e75--
"""

EMAIL_FROM_ML_CONTENT = """
From: Homer Simpson <homer@simpson.test>
Date: Wed, 15 Mar 2017 18:35:19 +0100
Message-ID: <CAN0378wA1V0VJg5OxyavB2uJgAimMc2ttGSc-yvWsXTaKqnKuw@simpson.test>
List-Id: "Test list" <list@test.org>
List-Archive: <http://lists.test.org/pipermail/test-list/>
Subject: Test
To: user@test.com
Content-Type: multipart/alternative; boundary=001a114420be4c231a054ac85e75

--001a114420be4c231a054ac85e75
Content-Type: text/plain; charset=UTF-8

pouet

--001a114420be4c231a054ac85e75
Content-Type: text/html; charset=UTF-8

<div dir="ltr">pouet<br></div>

--001a114420be4c231a054ac85e75--
"""


class EventsTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def test_domain_created_event(self):
        values = {
            "name": "domain.tld",
            "quota": 100,
            "default_mailbox_quota": 1,
            "create_dom_admin": False,
            "stepid": "step3",
            "type": "domain",
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        self.assertTrue(
            tr_models.Transport.objects.filter(pattern="autoreply.domain.tld").exists()
        )

    def test_domain_deleted_event(self):
        dom = admin_models.Domain.objects.get(name="test.com")
        self.ajax_post(reverse("admin:domain_delete", args=[dom.id]), {})
        with self.assertRaises(tr_models.Transport.DoesNotExist):
            tr_models.Transport.objects.get(pattern="autoreply.test.com")

    def test_domain_modified_event(self):
        values = {
            "name": "test.fr",
            "quota": 100,
            "default_mailbox_quota": 1,
            "enabled": True,
            "type": "domain",
        }
        dom = admin_models.Domain.objects.get(name="test.com")
        self.ajax_post(reverse("admin:domain_change", args=[dom.id]), values)
        self.assertTrue(
            tr_models.Transport.objects.filter(pattern="autoreply.test.fr").exists()
        )
        self.assertEqual(
            admin_models.Alias.objects.filter(domain=dom, internal=True).count(), 2
        )
        for alr in admin_models.AliasRecipient.objects.filter(
            address__contains="@test.fr"
        ):
            self.assertIn("autoreply.test.fr", alr.address)

    def test_armessage_postsave_event(self):
        values = {
            "username": "leon@test.com",
            "first_name": "Tester",
            "last_name": "Toto",
            "role": "SimpleUsers",
            "quota_act": True,
            "is_active": True,
            "email": "leon@test.com",
            "subject": "test",
            "content": "test",
            "enabled": True,
            "language": "en",
        }
        account = User.objects.get(username="user@test.com")
        self.ajax_post(reverse("admin:account_change", args=[account.id]), values)
        self.assertTrue(
            admin_models.AliasRecipient.objects.filter(
                alias__address="leon@test.com",
                alias__internal=True,
                address="leon@test.com@autoreply.test.com",
            ).exists()
        )
        values["enabled"] = False
        self.ajax_post(reverse("admin:account_change", args=[account.id]), values)
        self.assertFalse(
            admin_models.AliasRecipient.objects.filter(
                alias__address="leon@test.com",
                alias__internal=True,
                address="leon@test.com@autoreply.test.com",
            ).exists()
        )

    def test_mailbox_deleted_event(self):
        account = User.objects.get(username="user@test.com")
        self.ajax_post(reverse("admin:account_delete", args=[account.id]), {})
        self.assertFalse(
            admin_models.Alias.objects.filter(
                address="user@test.com", internal=True
            ).exists()
        )
        self.assertFalse(
            models.ARmessage.objects.filter(
                mbox__address="user", mbox__domain__name="test.com"
            ).exists()
        )

    def test_modify_mailbox_event(self):
        """Rename mailbox."""
        account = User.objects.get(username="user@test.com")
        factories.ARmessageFactory(mbox=account.mailbox)
        values = {
            "username": "leon@test.com",
            "first_name": "Tester",
            "last_name": "Toto",
            "role": "SimpleUsers",
            "quota_act": True,
            "is_active": True,
            "email": "leon@test.com",
            "subject": "test",
            "content": "test",
            "enabled": True,
            "language": "en",
        }
        self.ajax_post(reverse("admin:account_change", args=[account.id]), values)
        self.assertFalse(
            admin_models.AliasRecipient.objects.filter(
                alias__address="user@test.com",
                alias__internal=True,
                address="user@test.com@autoreply.test.com",
            ).exists()
        )
        self.assertTrue(
            admin_models.AliasRecipient.objects.filter(
                alias__address="leon@test.com",
                alias__internal=True,
                address="leon@test.com@autoreply.test.com",
            ).exists()
        )


class FormTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def setUp(self):
        """Initialize tests."""
        super().setUp()
        self.client.logout()
        self.client.login(username="user@test.com", password="toto")

    def test_form_display(self):
        """Check if form is displayed."""
        url = reverse("core:user_index")
        response = self.client.get(url)
        self.assertContains(response, "function autoreply_cb()")
        self.assertContains(response, 'name="autoreply"')

        response = self.ajax_get(reverse("autoreply"))
        self.assertIn("%(name)s", response["content"])

    def test_set_autoreply(self):
        values = {"subject": "test", "content": "I'm off", "enabled": True}
        self.ajax_post(reverse("autoreply"), values)
        account = User.objects.get(username="user@test.com")
        arm = models.ARmessage.objects.get(mbox=account.mailbox)
        self.assertEqual(arm.subject, "test")
        self.assertTrue(arm.enabled)
        self.assertFalse(arm.untildate)
        self.assertTrue(arm.fromdate)

    def test_set_autoreply_in_past(self):
        """Create an autoreply with from date expired."""
        fromdate = timezone.localtime(
            timezone.now().replace(year=2014, month=1, day=1, hour=12, microsecond=0)
        )
        values = {
            "subject": "test",
            "content": "I'm off",
            "enabled": True,
            "fromdate": fromdate.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.ajax_post(reverse("autoreply"), values)
        account = User.objects.get(username="user@test.com")
        arm = models.ARmessage.objects.get(mbox=account.mailbox)
        self.assertEqual(timezone.localtime(arm.fromdate), fromdate)

    def test_set_autoreply_dates(self):
        """Create an autoreply with from and to dates."""
        fromdate = timezone.localtime(timezone.now())
        untildate = fromdate + datetime.timedelta(days=1)
        values = {
            "subject": "test",
            "content": "I'm off",
            "enabled": True,
            "fromdate": fromdate.strftime("%Y-%m-%d %H:%M:%S"),
            "untildate": untildate.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.ajax_post(reverse("autoreply"), values)
        account = User.objects.get(username="user@test.com")
        arm = models.ARmessage.objects.get(mbox=account.mailbox)
        self.assertEqual(
            timezone.localtime(arm.fromdate), fromdate.replace(microsecond=0)
        )
        self.assertEqual(
            timezone.localtime(arm.untildate), untildate.replace(microsecond=0)
        )


class RepairTestCase(ModoTestCase):
    """Check repair command."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def test_management_command(self):
        """Check if problems are fixed."""
        mbox = admin_models.Mailbox.objects.get(user__username="user@test.com")
        alias = admin_models.Alias.objects.get(internal=True, address=mbox.full_address)
        arm = factories.ARmessageFactory(mbox=mbox, enabled=False)
        ar_address = f"{mbox.full_address}@autoreply.{mbox.domain.name}"
        admin_factories.AliasRecipientFactory(alias=alias, address=ar_address)
        management.call_command("modo", "repair", "--quiet")
        self.assertFalse(
            admin_models.AliasRecipient.objects.filter(address=ar_address).exists()
        )
        admin_factories.AliasRecipientFactory(alias=alias, address=ar_address)
        arm.delete()
        management.call_command("modo", "repair", "--quiet")
        self.assertFalse(
            admin_models.AliasRecipient.objects.filter(address=ar_address).exists()
        )


class ManagementCommandTestCase(ModoTestCase):
    """Management command related tests."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some data."""
        super().setUpTestData()
        admin_factories.populate_database()
        cls.account = User.objects.get(username="user@test.com")

    def setUp(self):
        """Replace stdin."""
        super().setUp()
        self.stdin = sys.stdin
        sys.stdin = StringIO(SIMPLE_EMAIL_CONTENT.strip())
        self.arm = factories.ARmessageFactory(mbox=self.account.mailbox)

    def tearDown(self):
        """Restore stdin."""
        sys.stdin = self.stdin

    def test_simple_case(self):
        """Check basic autoreply."""
        management.call_command("autoreply", "homer@simpson.test", "user@test.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(models.ARhistoric.objects.filter(armessage=self.arm).exists())

        # Try to send a new one
        sys.stdin.seek(0)
        management.call_command("autoreply", "homer@simpson.test", "user@test.com")
        self.assertEqual(len(mail.outbox), 1)

    def test_armessage_date_constraints(self):
        """Check date constraints."""
        account = User.objects.get(username="admin@test.com")
        arm = factories.ARmessageFactory(
            mbox=account.mailbox, fromdate=timezone.now() + relativedelta(days=1)
        )
        management.call_command("autoreply", "homer@simpson.com", "admin@test.com")
        self.assertEqual(len(mail.outbox), 0)

        arm.fromdate = timezone.now() - relativedelta(days=2)
        arm.untildate = timezone.now() - relativedelta(days=1)
        arm.save()
        sys.stdin.seek(0)
        management.call_command("autoreply", "homer@simpson.com", "admin@test.com")
        self.assertEqual(len(mail.outbox), 0)
        arm.refresh_from_db()
        self.assertFalse(arm.enabled)

    def test_recipient_does_not_exist(self):
        """Message received for non local recipient."""
        management.call_command("autoreply", "homer@simpson.com", "pouet@test.fr")
        self.assertEqual(len(mail.outbox), 0)

    def test_no_ar_message_defined(self):
        """No AR defined for local recipient."""
        management.call_command("autoreply", "homer@simpson.com", "admin@test.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_encoded_message(self):
        """Message received with encoded header"""
        sys.stdin = StringIO(ENCODED_EMAIL_SUBJECT.strip())
        management.call_command("autoreply", "homer@simpson.test", "user@test.com")
        self.assertEqual(len(mail.outbox), 1)

    def test_message_from_ml(self):
        """Message received from a mailing list."""
        sys.stdin = StringIO(EMAIL_FROM_ML_CONTENT.strip())
        management.call_command("autoreply", "mailer-daemon@list.test", "user@test.com")
        self.assertEqual(len(mail.outbox), 0)

        sys.stdin.seek(0)
        management.call_command("autoreply", "sender@list.test", "user@test.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_variable_substitution(self):
        """Check when message contains variables."""
        tz = timezone.get_current_timezone()
        self.arm.fromdate = datetime.datetime(2017, 12, 8, 14, 0, 0, 0).replace(
            tzinfo=tz
        )
        self.arm.content = "%(name)s %(fromdate)s %(untildate)s"
        self.arm.save()
        self.account.language = "fr"
        self.account.save(update_fields=["language"])
        management.call_command("autoreply", "homer@simpson.test", "user@test.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            "user@test.com 8 décembre 2017 14:00", mail.outbox[0].body.strip()
        )

    def test_untildate_substitution(self):
        """Check substitution of until date."""
        tz = timezone.get_current_timezone()
        self.arm.fromdate = datetime.datetime(2017, 12, 8, 14, 0, 0, 0).replace(
            tzinfo=tz
        )
        self.arm.untildate = timezone.now() + relativedelta(hours=1)
        self.arm.content = "%(name)s %(fromdate)s %(untildate)s"
        self.arm.save()
        management.call_command("autoreply", "homer@simpson.test", "user@test.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            "user@test.com Dec. 8, 2017, 2 p.m. {}".format(
                date_format(self.arm.untildate, "DATETIME_FORMAT")
            ),
            mail.outbox[0].body.strip(),
        )

    def test_message_with_bad_headers(self):
        """Message received with bad header (including newline)"""
        sys.stdin = StringIO(SIMPLE_EMAIL_CONTENT_WITH_BAD_HEADER.strip())
        management.call_command("autoreply", "homer@simpson.test", "user@test.com")
        self.assertEqual(len(mail.outbox), 1)

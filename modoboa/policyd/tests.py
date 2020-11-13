"""Policy daemon related tests."""

import asyncio
# from mock import patch
from asynctest import patch
from multiprocessing import Process
import socket
import time

import redis

from django import db
from django.conf import settings
from django.core.management import call_command
from django.test import TransactionTestCase
from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoTestCase, ParametersMixin
from modoboa.policyd import core as policyd_core

from . import constants


def start_policy_daemon():
    call_command("policy_daemon")


class RedisTestCaseMixin:
    """Mixin to provide a redis client."""

    def setUp(self):
        super().setUp()
        self.rclient = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_QUOTA_DB
        )
        self.rclient.set_response_callback("HGET", int)
        self.rclient.delete(constants.REDIS_HASHNAME)


class PolicyDaemonTestCase(
        RedisTestCaseMixin, ParametersMixin, TransactionTestCase):
    """Test cases for policy daemon.

    A redis instance is required to run those tests.
    """

    def setUp(self):
        super().setUp()
        call_command("load_initial_data")
        admin_factories.populate_database()
        self.admin = core_models.User.objects.get(username="user@test2.com")
        self.admin.role = "SuperAdmins"

        db.connections.close_all()
        patcher = patch("aiosmtplib.send")
        self.send_mock = patcher.start()
        self.process = Process(target=start_policy_daemon)
        self.process.daemon = True
        self.process.start()
        # Wait a bit for the daemon to start
        self.process.join(0.1)

    def set_domain_limit(self, name, value):
        """Set daily limit for domain."""
        domain = admin_models.Domain.objects.get(name=name)
        domain.message_limit = value
        domain.save()
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name),
            domain.message_limit
        )
        return domain

    def set_account_limit(self, name, value):
        """Set daily limit for account."""
        account = core_models.User.objects.get(username=name)
        mb = account.mailbox
        mb.message_limit = value
        mb.save()
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, account.email),
            mb.message_limit
        )
        return account

    def tearDown(self):
        self.process.terminate()
        self.process.join()

    def connect_to_daemon(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 9999))
        return s

    def test_daemon_starts(self):
        s = self.connect_to_daemon()
        s.send(b"protocol_state=RCPT\n\n")
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        s.close()

    def test_domain_limit(self):
        domain = self.set_domain_limit("test.com", 2)
        s = self.connect_to_daemon()

        # This one will be accepted
        s.send(b"""protocol_state=RCPT
sasl_username=user@test.com

""")
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name),
            domain.message_limit - 1
        )
        s.close()

        # This one will be accepted and will trigger a notification
        # but I can't check it yet
        s = self.connect_to_daemon()
        s.send(b"""protocol_state=RCPT
sasl_username=user@test.com

""")
        time.sleep(0.1)
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        s.close()

        # This one will be denied
        s = self.connect_to_daemon()
        s.send(b"""protocol_state=RCPT
sasl_username=user@test.com

""")
        res = s.recv(1024)
        self.assertEqual(
            res, b"action=defer_if_permit Daily limit reached, retry later\n\n"
        )

        s.close()

    def test_account_limit(self):
        account = self.set_account_limit("user@test.com", 2)
        s = self.connect_to_daemon()

        # This one will be accepted
        s.send(b"""protocol_state=RCPT
sasl_username=user@test.com

""")
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, account.email),
            account.mailbox.message_limit - 1
        )
        s.close()

        # This one will be accepted and will trigger a notification
        # but I can't check it yet
        s = self.connect_to_daemon()
        s.send(b"""protocol_state=RCPT
sasl_username=user@test.com

""")
        time.sleep(0.1)
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        s.close()

        # This one will be denied
        s = self.connect_to_daemon()
        s.send(b"""protocol_state=RCPT
sasl_username=user@test.com

""")
        res = s.recv(1024)
        self.assertEqual(
            res, b"action=defer_if_permit Daily limit reached, retry later\n\n"
        )

        s.close()

    def test_reset_counters(self):
        domain = self.set_domain_limit("test.com", 20)
        account = self.set_account_limit("user@test.com", 10)
        self.rclient.hset(constants.REDIS_HASHNAME, domain.name, 10)
        self.rclient.hset(constants.REDIS_HASHNAME, account.email, 0)
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

        async def run_test():
            await policyd_core.reset_counters()

        # Run the async test
        coro = asyncio.coroutine(run_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name), 20)
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, account.email), 10)


class ModelsTestCase(RedisTestCaseMixin, ModoTestCase):
    """Admin models test cases."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def test_domain_detail_view(self):
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.message_limit = 10
        domain.save()
        url = reverse("admin:domain_detail", args=[domain.pk])
        response = self.client.get(url)
        self.assertContains(response, "Message sending limit")

    def test_account_detail_view(self):
        account = core_models.User.objects.get(username="user@test.com")
        mb = account.mailbox
        mb.message_limit = 10
        mb.save()

        url = reverse("admin:account_detail", args=[account.pk])
        response = self.client.get(url)
        self.assertContains(response, "Message sending limit")

    def test_domain_signal_handler(self):
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.message_limit = 10
        domain.save()
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name),
            domain.message_limit
        )

        # Force constructor call to fill _loaded_values
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.message_limit = 50
        domain.save()
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name),
            domain.message_limit
        )

        domain.message_limit = None
        domain.save()
        self.assertFalse(
            self.rclient.hexists(constants.REDIS_HASHNAME, domain.name)
        )

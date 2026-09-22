"""Policy daemon related tests."""

import asyncio
from aiosmtplib import send
from unittest.mock import AsyncMock
import multiprocessing
from multiprocessing import Process
import os
import socket
import subprocess
import sys
import time

from django import db
from django.core.management import call_command
from django.test import tag, TransactionTestCase

from modoboa.admin import constants as admin_constants
from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
from modoboa.lib.redis import get_redis_connection
from modoboa.lib.tests import ModoAPITestCase, ParametersMixin
from modoboa.policyd import core as policyd_core

from . import constants

FAILURE_RESPONSE = b"action=defer_if_permit Daily limit reached, retry later\n\n"
multiprocessing.set_start_method("fork")


def start_policy_daemon(*args):
    call_command("policy_daemon", *args)


class RedisTestCaseMixin:
    """Mixin to provide a redis client."""

    def setUp(self):
        super().setUp()
        self.rclient = get_redis_connection()
        self.rclient.delete(constants.REDIS_HASHNAME)


class SocketActivationTestCase(TransactionTestCase):
    def test_socket_activation(self):
        self.assertTrue(os.path.basename(sys.argv[0]) == "manage.py")

        child_sock = socket.socket(socket.AF_UNIX)
        child_sock.bind("\0modoboa_test")
        child_sock.listen(1)
        client_sock = socket.socket(socket.AF_UNIX)
        client_sock.connect("\0modoboa_test")

        # Extract file descriptor without Python wrapper
        child_fd = child_sock.detach()

        def set_up_activation_env():
            """
            Called in child process before execve()
            """
            # Move file descriptor to number 3 if not already
            #
            # Must be inheritable to survive the imminent execve().
            if child_fd != 3:
                os.dup2(child_fd, 3, inheritable=True)
                os.close(child_fd)

            # Expose expected process environment variables
            os.environ["LISTEN_FDS"] = "1"
            os.environ["LISTEN_PID"] = str(os.getpid())

            # Child environment setup complete

        # Launch policy daemon as external process with socket activation process
        # environment
        #
        # To do this, `sock_b` is inherited to the child process, then moved to
        # FD number 3 and the expected environment variables are set. We expect
        # to be able to communicate with the policy daemon from `sock_a` after this.
        proc = subprocess.Popen(
            [sys.executable, sys.argv[0], "policy_daemon"],
            pass_fds=(3,),  # FD number post dup2!
            preexec_fn=set_up_activation_env,
        )
        try:
            os.close(child_fd)  # Now belongs to child

            client_sock.send(b"protocol_state=RCPT\n\n")
            res = client_sock.recv(1024)
            self.assertEqual(res, b"action=dunno\n\n")
        finally:
            client_sock.close()
            proc.terminate()
            proc.wait()

    def test_socket_path(self):
        try:
            os.remove("/tmp/modoboa_socket_path")
        except FileNotFoundError:
            pass

        process = Process(
            target=start_policy_daemon, args=("--socket", "/tmp/modoboa_socket_path")
        )
        process.daemon = True
        process.start()
        try:
            # Wait a bit for the daemon to start
            process.join(1.0)

            # Socket file should now exist
            self.assertTrue(os.path.exists("/tmp/modoboa_socket_path"))

            # Ensure that daemon is responding on other end of socket
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect("/tmp/modoboa_socket_path")
                s.send(b"protocol_state=RCPT\n\n")
                res = s.recv(1024)
                self.assertEqual(res, b"action=dunno\n\n")

            os.remove("/tmp/modoboa_socket_path")
        finally:
            process.terminate()
            process.join()


@tag("redis")
class PolicyDaemonTestCase(RedisTestCaseMixin, ParametersMixin, TransactionTestCase):
    """Test cases for policy daemon.

    A redis instance is required to run those tests.
    """

    databases = "__all__"

    def setUp(self):
        super().setUp()
        call_command("load_initial_data")
        admin_factories.populate_database()
        self.admin = core_models.User.objects.get(username="user@test2.com")
        self.admin.role = "SuperAdmins"

        db.connections.close_all()
        self.send_mock = AsyncMock(send)
        self.process = Process(target=start_policy_daemon)
        self.process.daemon = True
        self.process.start()
        # Wait a bit for the daemon to start
        self.process.join(1.0)

    def set_domain_limit(self, name, value):
        """Set daily limit for domain."""
        domain = admin_models.Domain.objects.get(name=name)
        domain.message_limit = value
        domain.save()
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name),
            domain.message_limit,
        )
        return domain

    def set_account_limit(self, name, value):
        """Set daily limit for account."""
        account = core_models.User.objects.get(username=name)
        mb = account.mailbox
        mb.message_limit = value
        mb.save()
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, account.email), mb.message_limit
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

    def test_connection_closed_on_timeout(self):
        """An idle client must be disconnected after the timeout."""
        s = self.connect_to_daemon()
        s.settimeout(10)
        try:
            self.assertEqual(s.recv(1024), b"")
        finally:
            s.close()

    def send_request(self, state, **attributes):
        """Send a policy request and return the answer."""
        attributes.setdefault("sasl_username", "user@test.com")
        request = f"protocol_state={state}\n"
        for name, value in attributes.items():
            request += f"{name}={value}\n"
        s = self.connect_to_daemon()
        try:
            s.send(request.encode() + b"\n")
            return s.recv(1024)
        finally:
            s.close()

    def _test_limit(self, key):
        # RCPT stage only checks limits: counter is not decremented
        res = self.send_request("RCPT")
        self.assertEqual(res, b"action=dunno\n\n")
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, key), 2)

        # Message accepted: counter is decremented
        res = self.send_request("END-OF-MESSAGE", recipient_count=1)
        self.assertEqual(res, b"action=dunno\n\n")
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, key), 1)

        # Too many recipients for the remaining counter: refused
        res = self.send_request("END-OF-MESSAGE", recipient_count=2)
        self.assertEqual(res, FAILURE_RESPONSE)
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, key), 1)

        # This one will be accepted and will trigger a notification
        # but I can't check it yet
        res = self.send_request("END-OF-MESSAGE", recipient_count=1)
        time.sleep(0.1)
        self.assertEqual(res, b"action=dunno\n\n")
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, key), 0)

        # Limit reached: refused at both stages
        self.assertEqual(self.send_request("RCPT"), FAILURE_RESPONSE)
        res = self.send_request("END-OF-MESSAGE", recipient_count=1)
        self.assertEqual(res, FAILURE_RESPONSE)
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, key), 0)

    def test_domain_limit(self):
        self.set_domain_limit("test.com", 2)
        self._test_limit("test.com")

    def test_account_limit(self):
        self.set_account_limit("user@test.com", 2)
        self._test_limit("user@test.com")

    def test_domain_and_account_limits(self):
        self.set_domain_limit("test.com", 10)
        self.set_account_limit("user@test.com", 1)
        res = self.send_request("END-OF-MESSAGE", recipient_count=2)
        self.assertEqual(res, FAILURE_RESPONSE)
        # No counter must be decremented if one of them refuses
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, "test.com"), 10)
        res = self.send_request("END-OF-MESSAGE", recipient_count=1)
        self.assertEqual(res, b"action=dunno\n\n")
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, "test.com"), 9)
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, "user@test.com"), 0
        )

    def test_reset_counters(self):
        domain = self.set_domain_limit("test.com", 20)
        account = self.set_account_limit("user@test.com", 10)
        self.rclient.hset(constants.REDIS_HASHNAME, domain.name, 10)
        self.rclient.hset(constants.REDIS_HASHNAME, account.email, 0)
        alarm = account.mailbox.alarms.create(
            domain=domain,
            title="Daily sending limit reached",
            internal_name=constants.SENDING_LIMIT_ALARM,
        )
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

        async def run_test():
            await policyd_core.reset_counters()

        # Run the async test
        event_loop.run_until_complete(run_test())
        event_loop.close()

        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, domain.name), 20)
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, account.email), 10)
        alarm.refresh_from_db()
        self.assertEqual(alarm.status, admin_constants.ALARM_CLOSED)
        self.assertIsNotNone(alarm.closed)


@tag("redis")
class ModelsTestCase(RedisTestCaseMixin, ModoAPITestCase):
    """Admin models test cases."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def test_domain_signal_handler(self):
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.message_limit = 10
        domain.save()
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name),
            domain.message_limit,
        )

        # Force constructor call to fill _loaded_values
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.message_limit = 50
        domain.save()
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name),
            domain.message_limit,
        )

        domain.message_limit = None
        domain.save()
        self.assertFalse(self.rclient.hexists(constants.REDIS_HASHNAME, domain.name))

    def test_domain_sent_messages_none_counter(self):
        """sent_messages returns 0 when Redis counter is missing."""
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.message_limit = 10
        domain.save()
        self.rclient.delete(constants.REDIS_HASHNAME)
        self.assertEqual(domain.sent_messages, 0)

    def test_mailbox_sent_messages_none_counter(self):
        """sent_messages returns 0 when Redis counter is missing."""
        account = core_models.User.objects.get(username="user@test.com")
        mb = account.mailbox
        mb.message_limit = 10
        mb.save()
        self.rclient.delete(constants.REDIS_HASHNAME)
        self.assertEqual(mb.sent_messages, 0)

    def test_domain_saved_twice(self):
        """Saving a new domain twice must not apply its limit twice."""
        domain = admin_models.Domain(name="new.com", quota=0, default_mailbox_quota=0)
        domain.message_limit = 10
        domain.save()
        domain.save()
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, "new.com"), 10)

        domain.message_limit = 20
        domain.save()
        domain.save()
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, "new.com"), 20)

    def test_mailbox_rename(self):
        """Counter must follow a renamed mailbox."""
        mb = admin_models.Mailbox.objects.get(address="user", domain__name="test.com")
        mb.message_limit = 10
        mb.save()
        self.rclient.hset(constants.REDIS_HASHNAME, "user@test.com", 7)

        mb = admin_models.Mailbox.objects.get(pk=mb.pk)
        mb.address = "renamed"
        mb.save()
        self.assertFalse(
            self.rclient.hexists(constants.REDIS_HASHNAME, "user@test.com")
        )
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, "renamed@test.com"), 7
        )

    def test_domain_rename(self):
        """Domain and mailbox counters must follow a renamed domain."""
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.message_limit = 20
        domain.save()
        mb = admin_models.Mailbox.objects.get(address="user", domain=domain)
        mb.message_limit = 10
        mb.save()
        self.rclient.hset(constants.REDIS_HASHNAME, "test.com", 15)
        self.rclient.hset(constants.REDIS_HASHNAME, "user@test.com", 7)

        domain = admin_models.Domain.objects.get(pk=domain.pk)
        domain.name = "renamed.com"
        domain.save()
        self.assertFalse(self.rclient.hexists(constants.REDIS_HASHNAME, "test.com"))
        self.assertFalse(
            self.rclient.hexists(constants.REDIS_HASHNAME, "user@test.com")
        )
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, "renamed.com"), 15)
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, "user@renamed.com"), 7
        )

    def test_counters_deleted(self):
        """Counters must be removed with their objects."""
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.message_limit = 20
        domain.save()
        mb = admin_models.Mailbox.objects.get(address="user", domain=domain)
        mb.message_limit = 10
        mb.save()

        domain.delete(core_models.User.objects.get(username="admin"))
        self.assertFalse(self.rclient.hexists(constants.REDIS_HASHNAME, "test.com"))
        self.assertFalse(
            self.rclient.hexists(constants.REDIS_HASHNAME, "user@test.com")
        )

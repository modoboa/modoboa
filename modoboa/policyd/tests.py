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
from django.test import TransactionTestCase

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
from modoboa.lib.redis import get_redis_connection
from modoboa.lib.tests import ModoAPITestCase, ParametersMixin
from modoboa.policyd import core as policyd_core

from . import constants

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

		process = Process(target=start_policy_daemon, args=("--socket", "/tmp/modoboa_socket_path"))
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

    def test_domain_limit(self):
        domain = self.set_domain_limit("test.com", 2)
        s = self.connect_to_daemon()

        # This one will be accepted
        s.send(
            b"""protocol_state=RCPT
sasl_username=user@test.com

"""
        )
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, domain.name),
            domain.message_limit - 1,
        )
        s.close()

        # This one will be accepted and will trigger a notification
        # but I can't check it yet
        s = self.connect_to_daemon()
        s.send(
            b"""protocol_state=RCPT
sasl_username=user@test.com

"""
        )
        time.sleep(0.1)
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        s.close()

        # This one will be denied
        s = self.connect_to_daemon()
        s.send(
            b"""protocol_state=RCPT
sasl_username=user@test.com

"""
        )
        res = s.recv(1024)
        self.assertEqual(
            res, b"action=defer_if_permit Daily limit reached, retry later\n\n"
        )

        s.close()

    def test_account_limit(self):
        account = self.set_account_limit("user@test.com", 2)
        s = self.connect_to_daemon()

        # This one will be accepted
        s.send(
            b"""protocol_state=RCPT
sasl_username=user@test.com

"""
        )
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        self.assertEqual(
            self.rclient.hget(constants.REDIS_HASHNAME, account.email),
            account.mailbox.message_limit - 1,
        )
        s.close()

        # This one will be accepted and will trigger a notification
        # but I can't check it yet
        s = self.connect_to_daemon()
        s.send(
            b"""protocol_state=RCPT
sasl_username=user@test.com

"""
        )
        time.sleep(0.1)
        res = s.recv(1024)
        self.assertEqual(res, b"action=dunno\n\n")
        s.close()

        # This one will be denied
        s = self.connect_to_daemon()
        s.send(
            b"""protocol_state=RCPT
sasl_username=user@test.com

"""
        )
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
        event_loop.run_until_complete(run_test())
        event_loop.close()

        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, domain.name), 20)
        self.assertEqual(self.rclient.hget(constants.REDIS_HASHNAME, account.email), 10)


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

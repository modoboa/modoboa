# coding: utf-8
"""Testing utilities."""

from __future__ import unicode_literals

import socket

from django.core import management
from django.test import TestCase

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from modoboa.core import models as core_models

from . import sysutils
from . import u2u_decode

try:
    s = socket.create_connection(('127.0.0.1', 25))
    s.close()
    NO_SMTP = False
except socket.error:
    NO_SMTP = True

try:
    import ldap  # NOQA
    NO_LDAP = False
except ImportError:
    NO_LDAP = True


class ParametersMixin(object):
    """Add tools to manage parameters."""

    @classmethod
    def setUpTestData(cls):
        """Set LocalConfig instance."""
        super(ParametersMixin, cls).setUpTestData()
        cls.localconfig = core_models.LocalConfig.objects.first()

    def set_global_parameter(self, name, value, app=None):
        """Set global parameter for the given app."""
        if app is None:
            app = sysutils.guess_extension_name()
        self.localconfig.parameters.set_value(name, value, app=app)
        self.localconfig.save()

    def set_global_parameters(self, parameters, app=None):
        """Set/update global parameters for the given app."""
        if app is None:
            app = sysutils.guess_extension_name()
        self.localconfig.parameters.set_values(parameters, app=app)
        self.localconfig.save()


class ModoTestCase(ParametersMixin, TestCase):
    """All test cases must inherit from this one."""

    @classmethod
    def setUpTestData(cls):
        """Create a default user."""
        super(ModoTestCase, cls).setUpTestData()
        management.call_command("load_initial_data")

    def setUp(self, username="admin", password="password"):
        """Initiate test context."""
        self.assertEqual(
            self.client.login(username=username, password=password), True)

    def ajax_request(self, method, url, params=None, status=200):
        if params is None:
            params = {}
        response = getattr(self.client, method)(
            url, params, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, status)
        return response.json()

    def ajax_post(self, *args, **kwargs):
        return self.ajax_request('post', *args, **kwargs)

    def ajax_put(self, *args, **kwargs):
        return self.ajax_request('put', *args, **kwargs)

    def ajax_delete(self, *args, **kwargs):
        return self.ajax_request('delete', *args, **kwargs)

    def ajax_get(self, *args, **kwargs):
        return self.ajax_request('get', *args, **kwargs)


class ModoAPITestCase(ParametersMixin, APITestCase):
    """All test cases must inherit from this one."""

    @classmethod
    def setUpTestData(cls):
        """Create a default user."""
        super(ModoAPITestCase, cls).setUpTestData()
        management.call_command("load_initial_data")
        cls.token = Token.objects.create(
            user=core_models.User.objects.get(username="admin"))

    def setUp(self):
        """Setup."""
        super(ModoAPITestCase, self).setUp()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)


class U2UTestCase(TestCase):
    """Test RFC1342 decoding utilities."""

    def test_header_decoding(self):
        """Simple decoding."""
        samples = [
            ("=?ISO-8859-15?Q?=20Profitez de tous les services en ligne sur "
             "impots.gouv.fr?=",
             "Profitez de tous les services en ligne sur impots.gouv.fr"),
            ("=?ISO-8859-1?Q?Accus=E9?= de =?ISO-8859-1?Q?r=E9ception?= de "
             "votre annonce",
             "Accusé de réception de votre annonce"),
            ("Sm=?ISO-8859-1?B?9g==?=rg=?ISO-8859-1?B?5Q==?=sbord",
             "Sm\xf6rg\xe5sbord"),
            # The following case currently fails because of the way we split
            # encoded words to parse them separately, which can lead to
            # unexpected unicode decode errors... I think it will work fine on
            # Python3
            # ("=?utf-8?B?VMOpbMOpcMOpYWdlIFZJTkNJIEF1dG9yb3V0ZXMgLSBFeHDD?=\n"
            #  "=?utf-8?B?qWRpdGlvbiBkZSB2b3RyZSBjb21tYW5kZSBOwrAgMjAxNzEyMDcw"
            #  "MDA1?=\n=?utf-8?B?MyBkdSAwNy8xMi8yMDE3IDE0OjQ5OjQx?=",
            #  "")
        ]
        for sample in samples:
            self.assertEqual(u2u_decode.u2u_decode(sample[0]), sample[1])

    def test_address_header_decoding(self):
        """Check address decoding."""
        mailsploit_sample = (
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q?=00?="
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?=@mailsploit.com")
        expected_result = (
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q??="
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?=@mailsploit.com")
        self.assertEqual(
            u2u_decode.decode_address(mailsploit_sample),
            ("", expected_result)
        )
        mailsploit_sample = (
            '"=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q?=0A=00?="\n'
            '<=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q?=0A=00?='
            '@mailsploit.com>')
        expected_result = (
            'potus@whitehouse.gov',
            '=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q??='
            '@mailsploit.com')
        self.assertEqual(
            u2u_decode.decode_address(mailsploit_sample),
            expected_result)

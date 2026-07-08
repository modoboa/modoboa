"""Dovecot access layer.

This module provides a small abstraction over the different ways to
communicate with Dovecot:

* ``cmd``: through the ``doveadm`` command line tool (default). It
  requires Dovecot to be installed on the same host than Modoboa.
* ``rest``: through the doveadm HTTP API. It allows Modoboa to manage a
  Dovecot server running on a different host.

The mode is controlled by the ``DOVECOT_OPERATION_MODE`` Django setting
(``"cmd"`` or ``"rest"``). The ``rest`` mode requires the following
additional settings:

* ``DOVEADM_API_URL``: url of the doveadm HTTP endpoint
  (eg. ``https://imap.example.com:8080/doveadm/v1``)
* ``DOVEADM_API_KEY``: value of the ``doveadm_api_key`` setting defined
  in the Dovecot configuration
* ``DOVEADM_API_TIMEOUT``: optional, request timeout in seconds
  (defaults to 10)
"""

import base64

from django.conf import settings
from django.utils.encoding import force_str

import requests

from modoboa.lib.sysutils import doveadm_cmd

DOVECOT_OPERATION_MODE_CMD = "cmd"
DOVECOT_OPERATION_MODE_REST = "rest"


class DoveadmError(Exception):
    """Raised when a doveadm operation fails, whatever the backend."""


class DoveadmCmdBackend:
    """Talk to Dovecot using the doveadm command line tool."""

    def get_user_home(self, address: str) -> str:
        """Return the home directory of the given user."""
        try:
            code, output = doveadm_cmd(["user", "-f", "home", address])
        except OSError as err:
            raise DoveadmError(str(err)) from err
        if code:
            raise DoveadmError(force_str(output))
        return force_str(output).strip()

    def move_message(
        self,
        user: str,
        destination: str,
        source_mailbox: str,
        header_name: str,
        header_value: str,
    ) -> None:
        """Move message(s) matching the given header to destination."""
        try:
            code, output = doveadm_cmd(
                [
                    "move",
                    "-u",
                    user,
                    destination,
                    "mailbox",
                    source_mailbox,
                    "header",
                    header_name,
                    header_value,
                ]
            )
        except OSError as err:
            raise DoveadmError(str(err)) from err
        if code:
            raise DoveadmError(force_str(output))

    def delete_mailbox_if_empty(self, user: str, mailbox: str) -> None:
        """Delete the given mailbox if it is empty. Best effort."""
        try:
            doveadm_cmd(["mailbox", "delete", "-u", user, "-s", "-e", mailbox])
        except OSError as err:
            raise DoveadmError(str(err)) from err

    def list_password_schemes(self) -> str:
        """Return password schemes supported by Dovecot."""
        try:
            code, output = doveadm_cmd(["pw", "-l"])
        except OSError as err:
            raise DoveadmError(str(err)) from err
        if code:
            raise DoveadmError(force_str(output))
        return force_str(output)


class DoveadmHTTPBackend:
    """Talk to Dovecot using the doveadm HTTP API."""

    def __init__(self):
        self.url = getattr(settings, "DOVEADM_API_URL", None)
        if not self.url:
            raise DoveadmError(
                "DOVEADM_API_URL setting is required when "
                "DOVECOT_OPERATION_MODE is set to 'rest'"
            )
        self.api_key = getattr(settings, "DOVEADM_API_KEY", None)
        if not self.api_key:
            raise DoveadmError(
                "DOVEADM_API_KEY setting is required when "
                "DOVECOT_OPERATION_MODE is set to 'rest'"
            )
        self.timeout = getattr(settings, "DOVEADM_API_TIMEOUT", 10)

    def _run_command(self, name: str, parameters: dict) -> list:
        """Run a doveadm command through the HTTP API.

        The API expects a list of commands ([name, parameters, tag]) and
        returns a list of responses ([type, data, tag]).
        """
        token = base64.b64encode(self.api_key.encode()).decode()
        headers = {
            "Authorization": f"X-Dovecot-API {token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                self.url,
                json=[[name, parameters, "c1"]],
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            content = response.json()
        except (requests.RequestException, ValueError) as err:
            raise DoveadmError(f"doveadm HTTP API request failed: {err}") from err
        try:
            rtype, data = content[0][0], content[0][1]
        except (IndexError, TypeError) as err:
            raise DoveadmError(
                f"unexpected response from doveadm HTTP API: {content}"
            ) from err
        if rtype == "error":
            raise DoveadmError(f"doveadm command {name} failed: {data}")
        return data

    def get_user_home(self, address: str) -> str:
        data = self._run_command("user", {"userMask": [address]})
        # Response is a list of userdb field dicts, possibly keyed by
        # user name depending on the Dovecot version.
        for entry in data:
            if not isinstance(entry, dict):
                continue
            if "home" in entry:
                return entry["home"]
            for value in entry.values():
                if isinstance(value, dict) and "home" in value:
                    return value["home"]
        raise DoveadmError(f"failed to retrieve home directory of {address}")

    def move_message(
        self,
        user: str,
        destination: str,
        source_mailbox: str,
        header_name: str,
        header_value: str,
    ) -> None:
        self._run_command(
            "move",
            {
                "user": user,
                "destinationMailbox": destination,
                "query": [
                    "mailbox",
                    source_mailbox,
                    "header",
                    header_name,
                    header_value,
                ],
            },
        )

    def delete_mailbox_if_empty(self, user: str, mailbox: str) -> None:
        self._run_command(
            "mailboxDelete",
            {
                "user": user,
                "mailbox": [mailbox],
                "requireEmpty": True,
                "subscriptions": True,
            },
        )

    def list_password_schemes(self) -> str:
        # 'doveadm pw' is a local command, not exposed through the HTTP
        # API. Use the DOVECOT_SUPPORTED_SCHEMES setting instead.
        raise DoveadmError(
            "listing password schemes is not supported by the doveadm HTTP API"
        )


def get_dovecot_operation_mode() -> str:
    """Return the configured operation mode."""
    return getattr(settings, "DOVECOT_OPERATION_MODE", DOVECOT_OPERATION_MODE_CMD)


def get_dovecot_backend():
    """Return a backend instance according to DOVECOT_OPERATION_MODE."""
    if get_dovecot_operation_mode() == DOVECOT_OPERATION_MODE_REST:
        return DoveadmHTTPBackend()
    return DoveadmCmdBackend()

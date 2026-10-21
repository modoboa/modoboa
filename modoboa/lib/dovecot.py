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
import json

from django.conf import settings
from django.utils.encoding import force_str

import requests

from modoboa.lib.sysutils import doveadm_cmd

DOVECOT_OPERATION_MODE_CMD = "cmd"
DOVECOT_OPERATION_MODE_REST = "rest"


class DoveadmError(Exception):
    """Raised when a doveadm operation fails, whatever the backend."""


def parse_acl(data: list) -> dict[str, list[str]]:
    """Return the rights by identifier from an 'acl get' result.

    Global entries are left out: doveadm can't change them.
    """
    try:
        return {
            entry["id"]: entry["rights"].split()
            for entry in data
            if not entry.get("global")
        }
    except (AttributeError, KeyError, TypeError) as err:
        raise DoveadmError(f"unexpected doveadm output: {data}") from err


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

    def _run_json(self, params: list[str], pinput: bytes | None = None) -> list:
        """Run a doveadm command and decode its JSON output."""
        try:
            code, output = doveadm_cmd(["-f", "json"] + params, pinput=pinput)
        except OSError as err:
            raise DoveadmError(str(err)) from err
        if code:
            raise DoveadmError(force_str(output))
        output = force_str(output)
        if not output.strip():
            # Commands without result print nothing, even in JSON mode
            return []
        try:
            return json.loads(output)
        except ValueError as err:
            raise DoveadmError(f"unexpected doveadm output: {output}") from err

    def list_sieve_scripts(self, user: str) -> list[str]:
        """Return the names of the user's Sieve scripts."""
        return [
            entry["script"] for entry in self._run_json(["sieve", "list", "-u", user])
        ]

    def get_sieve_script(self, user: str, name: str) -> str:
        """Return the content of a Sieve script."""
        data = self._run_json(["sieve", "get", "-u", user, name])
        try:
            return data[0]["sieve script"]
        except (IndexError, KeyError, TypeError) as err:
            raise DoveadmError(f"unexpected doveadm output: {data}") from err

    def put_sieve_script(self, user: str, name: str, content: str) -> None:
        """Create or replace a Sieve script. An active one stays active."""
        self._run_json(["sieve", "put", "-u", user, name], pinput=content.encode())

    def list_mailboxes(self, user: str) -> list[str]:
        """Return the names of the mailboxes a user can see."""
        return [
            entry["mailbox"]
            for entry in self._run_json(["mailbox", "list", "-u", user])
        ]

    def acl_get(self, user: str, mailbox: str) -> dict[str, list[str]]:
        """Return the ACL of a mailbox: rights by identifier."""
        return parse_acl(self._run_json(["acl", "get", "-u", user, mailbox]))

    def acl_set(
        self, user: str, mailbox: str, identifier: str, rights: list[str]
    ) -> None:
        """Replace the rights of an identifier (names, not RFC 4314 letters)."""
        self._run_json(["acl", "set", "-u", user, mailbox, identifier] + rights)

    def acl_delete(self, user: str, mailbox: str, identifier: str) -> None:
        """Remove the rights of an identifier."""
        self._run_json(["acl", "delete", "-u", user, mailbox, identifier])


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

    def list_sieve_scripts(self, user: str) -> list[str]:
        data = self._run_command("sieveList", {"user": user})
        return [entry["script"] for entry in data]

    def get_sieve_script(self, user: str, name: str) -> str:
        data = self._run_command("sieveGet", {"user": user, "scriptname": name})
        try:
            return data[0]["sieve script"]
        except (IndexError, KeyError, TypeError) as err:
            raise DoveadmError(f"unexpected doveadm output: {data}") from err

    def put_sieve_script(self, user: str, name: str, content: str) -> None:
        self._run_command(
            "sievePut", {"user": user, "scriptname": name, "file": content}
        )

    def list_mailboxes(self, user: str) -> list[str]:
        data = self._run_command("mailboxList", {"user": user})
        return [entry["mailbox"] for entry in data]

    def acl_get(self, user: str, mailbox: str) -> dict[str, list[str]]:
        return parse_acl(
            self._run_command("aclGet", {"user": user, "mailbox": mailbox})
        )

    def acl_set(
        self, user: str, mailbox: str, identifier: str, rights: list[str]
    ) -> None:
        self._run_command(
            "aclSet",
            {"user": user, "mailbox": mailbox, "id": identifier, "right": rights},
        )

    def acl_delete(self, user: str, mailbox: str, identifier: str) -> None:
        self._run_command(
            "aclDelete", {"user": user, "mailbox": mailbox, "id": identifier}
        )


def get_dovecot_operation_mode() -> str:
    """Return the configured operation mode."""
    return getattr(settings, "DOVECOT_OPERATION_MODE", DOVECOT_OPERATION_MODE_CMD)


def get_dovecot_backend():
    """Return a backend instance according to DOVECOT_OPERATION_MODE."""
    if get_dovecot_operation_mode() == DOVECOT_OPERATION_MODE_REST:
        return DoveadmHTTPBackend()
    return DoveadmCmdBackend()

"""Modoboa - Mail hosting made simple."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = None


def modoboa_admin():
    from modoboa.core.commands import handle_command_line

    handle_command_line()

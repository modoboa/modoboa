"""Modoboa - Mail hosting made simple."""

from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass


def modoboa_admin():
    from modoboa.core.commands import handle_command_line

    handle_command_line()

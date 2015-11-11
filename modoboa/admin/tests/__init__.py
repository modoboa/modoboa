"""modoboa-admin unit tests."""

from .account import AccountTestCase, PermissionsTestCase
from .alias import AliasTestCase
from .domain import DomainTestCase
from .domain_alias import DomainAliasTestCase
from .export import ExportTestCase
from .import_ import ImportTestCase
from .mapfiles import MapFilesTestCase
from .password_schemes import PasswordSchemesTestCase
from .user import ForwardTestCase

__all__ = [
    'AccountTestCase',
    'AliasTestCase',
    'DomainTestCase',
    'DomainAliasTestCase',
    'ExportTestCase',
    'ForwardTestCase',
    'ImportTestCase',
    'MapFilesTestCase',
    'PasswordSchemesTestCase',
    'PermissionsTestCase',
]

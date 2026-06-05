from modoboa.lib.tests import SimpleModoTestCase

from modoboa import __version__

class VersionTestCase(SimpleModoTestCase):

    def test_version(self):
        self.assertIsNot(__version__, None)
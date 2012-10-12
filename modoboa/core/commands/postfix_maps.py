
from modoboa.core.management import Command

class PostfixMapsCommand(Command):
    def __init__(self):
        super(PostfixMapsCommand, self).__init__()
        self._parser.add_argument('--dbtype', type=str, choices=['mysql', 'postgres'],
                                  help='The database type you use')

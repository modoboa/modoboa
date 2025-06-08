#!/usr/bin/env python


import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.settings")
    with open(os.path.join(os.path.dirname(__file__), "oidc_key")) as oidc_key_file:
        os.environ.setdefault("OIDC_RSA_PRIVATE_KEY", oidc_key_file.read())
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from None
        raise
    execute_from_command_line(sys.argv)

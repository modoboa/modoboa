#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
"""

from __future__ import unicode_literals

import io
from os import path

from setuptools import find_packages, setup


if __name__ == "__main__":
    HERE = path.abspath(path.dirname(__file__))
    with io.open(path.join(HERE, "README.rst"), encoding="utf-8") as readme:
        LONG_DESCRIPTION = readme.read()

    setup(
        name="modoboa",
        description="Mail hosting made simple",
        long_description=LONG_DESCRIPTION,
        license="ISC",
        url="http://modoboa.org/",
        author="Antoine Nguyen",
        author_email="tonio@ngyn.org",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Environment :: Web Environment",
            "Framework :: Django :: 1.11",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: ISC License (ISCL)",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Topic :: Communications :: Email",
            "Topic :: Internet :: WWW/HTTP",
        ],
        keywords="email",
        packages=find_packages(exclude=["doc", "test_data", "test_project"]),
        include_package_data=True,
        zip_safe=False,
        scripts=["bin/modoboa-admin.py"],
        install_requires=[
            "django>=1.11.8,<=1.11.99",
            "django-ckeditor==5.2.2",  # Django 1.11 support
            "django-reversion>=2.0.9",  # Django 1.11 support
            "django-subcommand2",
            "django-xforwardedfor-middleware>=2.0",  # Django >= 1.10 support
            "dj-database-url",
            "djangorestframework>=3.7.7",  # 3.7.4 - 3.7.6 had packaging issues
            "coreapi>=2.3.3",  # Required by Django Rest Framework
            "dnspython>=1.15.0",  # Improved PY3 support
            "feedparser",
            "gevent",
            "ipaddress; python_version < '3.3'",
            "jsonfield",
            "passlib>=1.7.0",
            "bcrypt",  # Optional dependency for passlib
            "progressbar33",
            "py-dateutil",
            "cryptography",
            "pytz",
            "requests",
            "rfc6266",
            "lxml",
            "backports.csv; python_version < '3.3'",
            "chardet",
        ],
        use_scm_version=True,
        setup_requires=["setuptools_scm"],
        extras_require={
            "ldap": [
                "django-auth-ldap>=1.3.0",
            ],
            "mysql": [
                "mysqlclient>=1.3.11",  # MariaDB >= 10.2 support
            ],
            "postgresql": [
                "psycopg2-binary>=2.7.4",  # Required by Django >= 1.11
            ],
            "dev": [
                "django-bower",
                "django-debug-toolbar",
            ],
            "test": [
                "factory-boy>=2.4",
                "mock; python_version < '3.3'",
                "httmock",
                "testfixtures",
                "tox",
            ],
        },
    )

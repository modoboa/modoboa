# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DB = os.environ.get("DB", "POSTGRESQL")

if DB == "MYSQL":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "modoboa",
            "USER": "root",
            "PASSWORD": "",
            "HOST": "localhost",
            "PORT": "",
            "ATOMIC_REQUESTS": True,
            # MySQL's Strict Mode fixes many data integrity problems in MySQL,
            # such as data truncation upon insertion, by escalating warnings
            # into errors. It is strongly recommended you activate it.
            # MySQL >= 5.7 set STRICT_TRANS_TABLES by default
            # See:
            # https://docs.djangoproject.com/en/1.11/ref/databases/#mysql-sql-mode
            "OPTIONS": {
                "init_command": (
                    "SET sql_mode = 'STRICT_TRANS_TABLES';"
                    "SET innodb_strict_mode = ON;"
                ),
                "charset": "utf8",
            },
            "TEST": {
                "CHARSET": "utf8",
                "COLLATION": "utf8_unicode_ci",
            },
        },
    }
elif DB == "SQLITE":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "modoboa.db",
            "PORT": "",
            "ATOMIC_REQUESTS": True,
        },
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "modoboa",
            "USER": "postgres",
            "PASSWORD": "",
            "HOST": "localhost",
            "PORT": "",
            "ATOMIC_REQUESTS": True,
            "OPTIONS": {
                    "client_encoding": "UTF8",
            },
            "TEST": {
                "CHARSET": "UTF8",
            },
        },
    }

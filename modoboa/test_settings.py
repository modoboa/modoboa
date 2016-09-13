# -*- coding: utf-8 -*-
import os

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DB = os.environ.get('DB', 'POSTGRES')

if DB == 'MYSQL':
    DATABASES = {

        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'modoboa_test',
            'USER': 'modoboa',
            'PASSWORD': 'modoboa',
            'HOST': 'localhost',
            'PORT': '',
            'ATOMIC_REQUESTS': True,

        },

    }
if DB == 'SQLITE':
    DATABASES = {

        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'modoboa_test.db',
            'PORT': '',
            'ATOMIC_REQUESTS': True,

        },

    }
else:
    DATABASES = {

        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'modoboa_test',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '',
            'ATOMIC_REQUESTS': True,

        },

    }

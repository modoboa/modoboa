import os

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DB = os.environ.get("DB", "postgres").lower()

if DB == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "modoboa",
            "USER": os.environ.get("MYSQL_USER", "root"),
            "PASSWORD": os.environ.get("MYSQL_PASSWORD", "root"),
            "HOST": "127.0.0.1",
            "PORT": os.environ.get("MYSQL_PORT", "3306"),
            "ATOMIC_REQUESTS": True,
            # MySQL's Strict Mode fixes many data integrity problems in MySQL,
            # such as data truncation upon insertion, by escalating warnings
            # into errors. It is strongly recommended you activate it.
            # MySQL >= 5.7 set STRICT_TRANS_TABLES by default
            # See:
            # https://docs.djangoproject.com/en/2.2/ref/databases/#mysql-sql-mode
            "OPTIONS": {
                "init_command": (
                    "SET sql_mode = 'STRICT_TRANS_TABLES';"
                    "SET innodb_strict_mode = ON;"
                ),
                "charset": "utf8",
                "connect_timeout": 10,
            },
            "TEST": {
                "CHARSET": "utf8",
                "COLLATION": "utf8_unicode_ci",
            },
        },
    }
elif DB == "sqlite":
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
            "PASSWORD": "postgres",
            "HOST": "localhost",
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "ATOMIC_REQUESTS": True,
            "OPTIONS": {
                "client_encoding": "UTF8",
                "sslmode": "disable"
            },
            "TEST": {
                "CHARSET": "UTF8",
            },
        },
    }

# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "modoboa_contacts_category"},
        ),
        migrations.CreateModel(
            name="Contact",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("first_name", models.CharField(blank=True, max_length=30)),
                ("last_name", models.CharField(blank=True, max_length=30)),
                ("display_name", models.CharField(blank=True, max_length=60)),
                ("birth_date", models.DateField(null=True)),
                ("company", models.CharField(blank=True, max_length=100)),
                ("position", models.CharField(blank=True, max_length=200)),
                ("address", models.CharField(blank=True, max_length=200)),
                ("zipcode", models.CharField(blank=True, max_length=15)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("state", models.CharField(blank=True, max_length=100)),
                ("note", models.TextField(blank=True)),
                (
                    "categories",
                    models.ManyToManyField(blank=True, to="contacts.Category"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "modoboa_contacts_contact"},
        ),
        migrations.CreateModel(
            name="EmailAddress",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("address", models.EmailField(max_length=254)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            (b"home", "Home"),
                            (b"work", "Work"),
                            (b"other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="emails",
                        to="contacts.Contact",
                    ),
                ),
            ],
            options={"db_table": "modoboa_contacts_emailaddress"},
        ),
        migrations.CreateModel(
            name="PhoneNumber",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("number", models.CharField(max_length=40)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            (b"home", "Home"),
                            (b"work", "Work"),
                            (b"other", "Other"),
                            (b"main", "Main"),
                            (b"cellular", "Cellular"),
                            (b"fax", "Fax"),
                            (b"pager", "Pager"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="phone_numbers",
                        to="contacts.Contact",
                    ),
                ),
            ],
            options={"db_table": "modoboa_contacts_phonenumber"},
        ),
    ]

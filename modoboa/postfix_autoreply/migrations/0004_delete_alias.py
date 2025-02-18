# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("postfix_autoreply", "0003_move_aliases"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Alias",
        ),
    ]

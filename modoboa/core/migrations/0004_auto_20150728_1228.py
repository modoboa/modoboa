from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_user_master_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(db_index=True, max_length=254, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="user",
            name="is_active",
            field=models.BooleanField(default=True, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="user",
            name="is_local",
            field=models.BooleanField(default=True, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="user",
            name="is_staff",
            field=models.BooleanField(default=False, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="user",
            name="master_user",
            field=models.BooleanField(
                default=False,
                help_text="Allow this administrator to access user mailboxes",
                verbose_name="Allow mailboxes access",
            ),
            preserve_default=True,
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                fields=("email", "is_active"),
                name="core_user_email_c0c03f_idx",
            ),
        ),
    ]

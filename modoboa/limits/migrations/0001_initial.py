from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Limit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('curvalue', models.IntegerField(default=0)),
                ('maxvalue', models.IntegerField(default=-2)),
            ],
            options={
                'db_table': 'limits_limit',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LimitsPool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'limits_limitspool',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='limit',
            name='pool',
            field=models.ForeignKey(to='limits.LimitsPool', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='limit',
            unique_together=set([('name', 'pool')]),
        ),
    ]

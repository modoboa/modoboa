from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20150728_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='language',
            field=models.CharField(default=b'en', help_text='Prefered language to display pages.', max_length=10, choices=[(b'cs', '\u010de\u0161tina'), (b'de', 'deutsch'), (b'en', 'english'), (b'es', 'espa\xf1ol'), (b'fr', 'fran\xe7ais'), (b'it', 'italiano'), (b'nl', 'nederlands'), (b'pt_PT', 'portugu\xeas'), (b'pt_BR', 'portugu\xeas (BR)'), (b'ru', '\u0440\u0443\u0441\u0441\u043a\u0438\u0439'), (b'sv', 'svenska')]),
            preserve_default=True,
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transforms', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transform',
            name='owners',
            field=models.ManyToManyField(to='users.User'),
            preserve_default=True,
        ),
    ]

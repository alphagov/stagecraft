# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0002_auto_20150615_0916'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboard',
            name='owners',
            field=models.ManyToManyField(to='users.User'),
            preserve_default=True,
        ),
    ]

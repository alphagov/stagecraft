# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transforms', '0002_transform_owners'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transform',
            name='owners',
            field=models.ManyToManyField(to='users.User', blank=True),
        ),
    ]

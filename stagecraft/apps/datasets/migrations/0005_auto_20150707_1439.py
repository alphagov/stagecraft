# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0004_copy_user_datasets'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='owners',
            field=models.ManyToManyField(to='users.User', blank=True),
        ),
    ]

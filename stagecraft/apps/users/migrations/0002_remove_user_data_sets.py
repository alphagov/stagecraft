# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('datasets', '0004_copy_user_datasets'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='data_sets',
        ),
    ]

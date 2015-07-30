# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collectors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='collector',
            name='slug',
            field=models.SlugField(default='', unique=True, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collectortype',
            name='slug',
            field=models.SlugField(default='', unique=True, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='datasource',
            name='slug',
            field=models.SlugField(default='', unique=True, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='provider',
            name='slug',
            field=models.SlugField(default='', unique=True, max_length=100),
            preserve_default=False,
        ),
    ]

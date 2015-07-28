# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('collectors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectortype',
            name='slug',
            field=models.CharField(default='', unique=True, max_length=256, validators=[django.core.validators.RegexValidator(b'^[-a-z0-9]+$', message=b'Slug can only contain lower case letters, numbers or hyphens')]),
            preserve_default=False,
        ),
    ]

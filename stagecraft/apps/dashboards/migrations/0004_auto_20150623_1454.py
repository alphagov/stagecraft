# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0003_dashboard_owners'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dashboard',
            name='slug',
            field=models.CharField(unique=True, max_length=1000, validators=[django.core.validators.RegexValidator('^[-a-z0-9]+$', message='Slug can only contain lower case letters, numbers or hyphens')]),
        ),
    ]

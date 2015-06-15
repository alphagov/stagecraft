# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='module',
            name='options',
            field=jsonfield.fields.JSONField(default={}, blank=True),
        ),
        migrations.AlterField(
            model_name='moduletype',
            name='schema',
            field=jsonfield.fields.JSONField(default={}),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('data_sets', models.ManyToManyField(to='datasets.DataSet', blank=True)),
            ],
            options={
                'ordering': ['email'],
            },
            bases=(models.Model,),
        ),
    ]

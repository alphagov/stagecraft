# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import uuidfield.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transform',
            fields=[
                ('id', uuidfield.fields.UUIDField(primary_key=True, auto=True, serialize=False, hyphenate=True)),
                ('query_parameters', jsonfield.fields.JSONField(default={}, blank=True)),
                ('options', jsonfield.fields.JSONField(default={}, blank=True)),
                ('input_group', models.ForeignKey(related_name='+', blank=True, to='datasets.DataGroup', null=True)),
                ('input_type', models.ForeignKey(related_name='+', to='datasets.DataType')),
                ('output_group', models.ForeignKey(related_name='+', blank=True, to='datasets.DataGroup', null=True)),
                ('output_type', models.ForeignKey(related_name='+', to='datasets.DataType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TransformType',
            fields=[
                ('id', uuidfield.fields.UUIDField(primary_key=True, auto=True, serialize=False, hyphenate=True)),
                ('name', models.CharField(unique=True, max_length=25)),
                ('schema', jsonfield.fields.JSONField(default={}, blank=True)),
                ('function', models.CharField(unique=True, max_length=200, validators=[django.core.validators.RegexValidator(b'^[a-z_\\.]+$', message=b'Transform function has to consist of lowercaseletters, underscores or dots')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='transform',
            name='type',
            field=models.ForeignKey(to='transforms.TransformType'),
            preserve_default=True,
        ),
    ]

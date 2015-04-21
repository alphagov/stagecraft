# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuidfield.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', uuidfield.fields.UUIDField(primary_key=True, auto=True, serialize=False, hyphenate=True)),
                ('name', models.CharField(max_length=256)),
                ('abbreviation', models.CharField(max_length=50, null=True, blank=True)),
                ('slug', models.CharField(default='', max_length=150, validators=[django.core.validators.RegexValidator(b'^[-a-z0-9]+$', message='Slug can only contain lower case letters, numbers or hyphens')])),
                ('parents', models.ManyToManyField(to='organisation.Node')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NodeType',
            fields=[
                ('id', uuidfield.fields.UUIDField(primary_key=True, auto=True, serialize=False, hyphenate=True)),
                ('name', models.CharField(unique=True, max_length=256)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='node',
            name='typeOf',
            field=models.ForeignKey(to='organisation.NodeType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='node',
            unique_together=set([('name', 'slug', 'typeOf')]),
        ),
    ]

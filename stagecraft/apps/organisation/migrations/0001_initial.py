# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('abbreviation', models.CharField(max_length=50, null=True, blank=True)),
                ('slug', models.CharField(default=b'', max_length=150, validators=[django.core.validators.RegexValidator(b'^[-a-z0-9]+$', message=b'Slug can only contain lower case letters, numbers or hyphens')])),
                ('parents', models.ManyToManyField(to='organisation.Node')),
            ],
        ),
        migrations.CreateModel(
            name='NodeType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=256)),
            ],
        ),
        migrations.AddField(
            model_name='node',
            name='typeOf',
            field=models.ForeignKey(to='organisation.NodeType'),
        ),
        migrations.AlterUniqueTogether(
            name='node',
            unique_together=set([('name', 'slug', 'typeOf')]),
        ),
    ]

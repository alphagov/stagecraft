# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django_field_cryptography.fields
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_user_data_sets'),
        ('datasets', '0005_auto_20150707_1439'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collector',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('query', jsonfield.fields.JSONField(default={}, blank=True)),
                ('options', jsonfield.fields.JSONField(default={}, blank=True)),
                ('data_set', models.ForeignKey(to='datasets.DataSet')),
            ],
        ),
        migrations.CreateModel(
            name='CollectorType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=256)),
                ('entry_point', models.CharField(unique=True, max_length=200, validators=[django.core.validators.RegexValidator(b'^[a-z0-9_\\.]+$', message=b'Collector entry point function has to consist of lowercaseletters, underscores or dots')])),
                ('query_schema', jsonfield.fields.JSONField(default={}, blank=True)),
                ('options_schema', jsonfield.fields.JSONField(default={}, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=256)),
                ('credentials', django_field_cryptography.fields.EncryptedTextField(default=b'{}')),
                ('owners', models.ManyToManyField(to='users.User', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Provider',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=256)),
                ('credentials_schema', jsonfield.fields.JSONField(default={}, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='datasource',
            name='provider',
            field=models.ForeignKey(to='collectors.Provider'),
        ),
        migrations.AddField(
            model_name='collectortype',
            name='provider',
            field=models.ForeignKey(to='collectors.Provider'),
        ),
        migrations.AddField(
            model_name='collector',
            name='data_source',
            field=models.ForeignKey(to='collectors.DataSource'),
        ),
        migrations.AddField(
            model_name='collector',
            name='owners',
            field=models.ManyToManyField(to='users.User', blank=True),
        ),
        migrations.AddField(
            model_name='collector',
            name='type',
            field=models.ForeignKey(to='collectors.CollectorType'),
        ),
    ]

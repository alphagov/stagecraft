# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import ArrayField
from jsonfield import JSONField
from django.db import models, migrations
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0001_initial'),
        ('organisation', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('slug', models.CharField(unique=True, max_length=90, validators=[django.core.validators.RegexValidator('^[-a-z0-9]+$', message='Slug can only contain lower case letters, numbers or hyphens')])),
                ('dashboard_type', models.CharField(default='transaction', max_length=30, choices=[('transaction', 'transaction'), ('high-volume-transaction', 'high-volume-transaction'), ('service-group', 'service-group'), ('agency', 'agency'), ('department', 'department'), ('content', 'content'), ('other', 'other')])),
                ('page_type', models.CharField(default='dashboard', max_length=80)),
                ('status', models.CharField(default='unpublished', max_length=30)),
                ('title', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=500, blank=True)),
                ('description_extra', models.CharField(max_length=400, blank=True)),
                ('costs', models.CharField(max_length=1500, blank=True)),
                ('other_notes', models.CharField(max_length=1000, blank=True)),
                ('customer_type', models.CharField(default='', max_length=30, blank=True, choices=[('', ''), ('Business', 'Business'), ('Individuals', 'Individuals'), ('Business and individuals', 'Business and individuals'), ('Charity', 'Charity')])),
                ('business_model', models.CharField(default='', max_length=31, blank=True, choices=[('', ''), ('Department budget', 'Department budget'), ('Fees and charges', 'Fees and charges'), ('Taxpayers', 'Taxpayers'), ('Fees and charges, and taxpayers', 'Fees and charges, and taxpayers')])),
                ('improve_dashboard_message', models.BooleanField(default=True)),
                ('strapline', models.CharField(default='Dashboard', max_length=40, choices=[('Dashboard', 'Dashboard'), ('Service dashboard', 'Service dashboard'), ('Content dashboard', 'Content dashboard'), ('Performance', 'Performance'), ('Policy dashboard', 'Policy dashboard'), ('Public sector purchasing dashboard', 'Public sector purchasing dashboard'), ('Topic Explorer', 'Topic Explorer'), ('Service Explorer', 'Service Explorer')])),
                ('tagline', models.CharField(max_length=400, blank=True)),
                ('_organisation', models.ForeignKey(db_column='organisation_id', blank=True, to='organisation.Node', null=True)),
                ('agency_cache', models.ForeignKey(related_name='dashboards_owned_by_agency', blank=True, to='organisation.Node', null=True)),
                ('department_cache', models.ForeignKey(related_name='dashboards_owned_by_department', blank=True, to='organisation.Node', null=True)),
                ('service_cache', models.ForeignKey(related_name='dashboards_owned_by_service', blank=True, to='organisation.Node', null=True)),
                ('transaction_cache', models.ForeignKey(related_name='dashboards_owned_by_transaction', blank=True, to='organisation.Node', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('link_type', models.CharField(max_length=20, choices=[('transaction', 'transaction'), ('other', 'other')])),
                ('dashboard', models.ForeignKey(to='dashboards.Dashboard')),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('slug', models.CharField(max_length=60, validators=[django.core.validators.RegexValidator('^[-a-z0-9]+$', message='Slug can only contain lower case letters, numbers or hyphens')])),
                ('title', models.CharField(max_length=60)),
                ('description', models.CharField(max_length=200, blank=True)),
                ('info', ArrayField(base_field=models.TextField(blank=True), size=None)),
                ('options', JSONField(blank=True)),
                ('query_parameters', JSONField(null=True, blank=True)),
                ('order', models.IntegerField()),
                ('dashboard', models.ForeignKey(to='dashboards.Dashboard')),
                ('data_set', models.ForeignKey(blank=True, to='datasets.DataSet', null=True)),
                ('parent', models.ForeignKey(blank=True, to='dashboards.Module', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ModuleType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=25, validators=[django.core.validators.RegexValidator('^[a-z_]+$', message='Module type name can only contain lowercase letters, numbers or underscores')])),
                ('schema', JSONField()),
            ],
        ),
        migrations.AddField(
            model_name='module',
            name='type',
            field=models.ForeignKey(to='dashboards.ModuleType'),
        ),
        migrations.AlterUniqueTogether(
            name='module',
            unique_together=set([('dashboard', 'slug')]),
        ),
    ]

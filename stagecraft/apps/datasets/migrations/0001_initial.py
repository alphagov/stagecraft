# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import ArrayField
from django.db import models, migrations
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(unique=True, max_length=60, validators=[django.core.validators.RegexValidator('^[a-z0-9\\-]+$', 'Only lowercase alphanumeric characters and hyphens are allowed.')])),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(validators=[django.core.validators.RegexValidator('^[a-z0-9_]+$', 'Only lowercase alphanumeric characters and underscores are allowed.')], max_length=200, blank=True, help_text="\n        This will be automatically generated to use the\n        format 'data_group_data_type'\n        e.g. `carers_allowance_customer_satisfaction`\n        ", unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created (UTC)')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified (UTC)')),
                ('raw_queries_allowed', models.BooleanField(default=True, editable=False)),
                ('bearer_token', models.CharField(default='', help_text="\n        - If it's for an internal collector or customer-satisfaction,\n        copy the token from another data-set of the same data type.<br/>\n        - If it's for a new type then copy from a data-set of the same\n        collector, or from a content data-set in the case of new content\n        data-sets. (If you're not sure what this means ask a developer).<br/>\n        - Otherwise, generate a new token with the link provided.\n        ", max_length=255, blank=True)),
                ('upload_format', models.CharField(help_text="\n        [OPTIONAL FIELD] Only fill in this field if\n        data is being uploaded via the admin app.</br>\n        - Write 'excel' or 'csv'\n        ", max_length=255, blank=True)),
                ('upload_filters', models.TextField(help_text='\n        A comma separated list of filters.\n        If users manually upload CSV files you can leave this blank.<br/>\n        If users manually upload Excel files with the data in the first\n        sheet (a common scenario) this should be\n        "backdrop.core.upload.filters.first_sheet_filter".<br/>\n        Other possible values are:\n        "backdrop.contrib.evl_upload_filters.ceg_volumes",\n        "backdrop.contrib.evl_upload_filters.channel_volumetrics",\n        "backdrop.contrib.evl_upload_filters.customer_satisfaction",\n        "backdrop.contrib.evl_upload_filters.service_failures",\n        "backdrop.contrib.evl_upload_filters.service_volumetrics" and\n        "backdrop.contrib.evl_upload_filters.volumetrics"\n        ', blank=True)),
                ('auto_ids', models.TextField(help_text="\n        [OPTIONAL FIELD] If you're doing a CSV or Excel upload, and the data\n        may be cumulative, you should complete this field to avoid the risk of\n        duplicate records.</br>\n        Write a comma separated list of fields to turn into a unique id, eg:\n        <code>_timestamp,service,channel</code></br>\n        This should list every field name that, when combined, could identify a\n        unique record. If this is left blank Backdrop won't be able to identify\n        duplicate records which will result in double counting.\n        ", blank=True)),
                ('queryable', models.BooleanField(default=True, help_text='\n        Leave this ticked unless told otherwise.\n        ')),
                ('realtime', models.BooleanField(default=False, help_text='\n        Tick this box if this data-set is collecting realtime data.\n        e.g. current visitor counts\n        ')),
                ('capped_size', models.PositiveIntegerField(default=None, help_text='\n        [OPTIONAL FIELD] Only fill this in if the data-set is realtime.<br/>\n        Set this to 4194304 (4mb), which gives us just over two weeks of data.\n        ', null=True, blank=True)),
                ('max_age_expected', models.PositiveIntegerField(default=86400, help_text="\n        [OPTIONAL FIELD] How often do you expect the data to be updated?\n        (<strong>in seconds</strong>)<br/>\n        This is used for monitoring so we can tell when data hasn't been\n        updated. If this is left blank the data-set will not be monitored.<br/>\n        Commonly used values are:<br/>\n        - <strong>360</strong> (every 5 minutes)<br/>\n        - <strong>9000</strong> (for hourly data)<br/>\n        - <strong>180000</strong> (for daily data)<br/>\n        - <strong>1300000</strong> (for weekly data)<br/>\n        - <strong>5200000</strong> (for monthly data)<br/>\n        - <strong>15600000</strong> (for quarterly data)<br/>\n        You can choose your own value if the ones above don't work for your\n        case.\n        ", null=True, blank=True)),
                ('published', models.BooleanField(default=False, help_text='\n        Set to published if this data-set should be publicly available\n        ')),
                ('data_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='datasets.DataGroup', help_text="\n        - Normally this will be the name of the service<br/>\n        - e.g. 'carers-allowance'<br/>\n        - Add a data group first if it doesn't already exist</br>\n        (This should match the slug on GOV.UK when possible)</br>\n        - Use hyphens to separate words.\n        ")),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(unique=True, max_length=60, validators=[django.core.validators.RegexValidator('^[a-z0-9\\-]+$', 'Only lowercase alphanumeric characters and hyphens are allowed.')])),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OAuthUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('access_token', models.CharField(unique=True, max_length=255)),
                ('uid', models.CharField(max_length=255, db_index=True)),
                ('email', models.EmailField(max_length=75)),
                ('permissions', ArrayField(base_field=models.CharField(max_length=255))),
                ('expires_at', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='dataset',
            name='data_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='datasets.DataType', help_text="\n        The type of data this data-set will be collecting.\n        e.g. 'customer-satisfaction' </br>\n        - Use hyphens to separate words.\n        "),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dataset',
            unique_together=set([('data_group', 'data_type')]),
        ),
    ]

# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.db.models import Q
import re
import random
from itertools import repeat

DATASET_NAME_EXCLUSIONS = [
    'driving_test_practical_transactions_by_channel',
    'evl_customer_satisfaction',
    'gcloud_sales',
    'patent_renewal_journey_completion',
    'patent_renewal_transactions_by_channel',
    'solihull_local_authority_missed_bin_by_ward',
    'solihull_local_authority_transactions_by_channel',
    'student_finance_transactions_by_channel',
]

BEARER_TOKEN_LENGTH = 64


def get_dataset_emails(dataset):
    return [u.email for u in dataset.backdropuser_set.all()]


def generate_bearer_token():
    chars = "abcdefghjkmnpqrstuvwxyz23456789"
    return "".join(map(random.choice, repeat(chars, BEARER_TOKEN_LENGTH)))


def delete_all_users(dataset):
    print('deleting all users for {} - users {}'.format(
        dataset.name, get_dataset_emails(dataset)))
    dataset.backdropuser_set.clear()


def add_bearer_token(dataset):
    dataset.bearer_token = generate_bearer_token()
    print('adding bearer token for {}'.format(dataset.name))
    dataset.save()


def get_datasets_with_users_and_bearer_tokens(orm):
    return orm['datasets.DataSet'].\
        objects.\
        exclude(bearer_token__exact='').\
        exclude(name__in=DATASET_NAME_EXCLUSIONS).\
        filter(backdropuser__email__isnull=False).\
        distinct()


def get_datasets_without_bearer_tokens(orm):
    return orm['datasets.DataSet'].\
        objects.\
        filter(Q(bearer_token__exact='') | Q( bearer_token__isnull=True)).\
        distinct()


class Migration(DataMigration):

    def forwards(self, orm):
        map(delete_all_users, get_datasets_with_users_and_bearer_tokens(orm))
        map(add_bearer_token, get_datasets_without_bearer_tokens(orm))

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'datasets.backdropuser': {
            'Meta': {'ordering': "[u'email']", 'object_name': 'BackdropUser'},
            'data_sets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['datasets.DataSet']", 'symmetrical': 'False', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '254'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'datasets.datagroup': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'datasets.dataset': {
            'Meta': {'ordering': "[u'name']", 'unique_together': "([u'data_group', u'data_type'],)", 'object_name': 'DataSet'},
            'auto_ids': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bearer_token': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'capped_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataGroup']", 'on_delete': 'models.PROTECT'}),
            'data_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataType']", 'on_delete': 'models.PROTECT'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_age_expected': ('django.db.models.fields.PositiveIntegerField', [], {'default': '86400', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'queryable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'raw_queries_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'realtime': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'upload_filters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'upload_format': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'datasets.datatype': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataType'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['datasets']
    symmetrical = True

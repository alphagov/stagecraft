# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'DataSet.name'
        db.alter_column(u'datasets_dataset', 'name', self.gf(
            'django.db.models.fields.SlugField')(unique=True, max_length=200))

    def backwards(self, orm):

        # Changing field 'DataSet.name'
        db.alter_column(u'datasets_dataset', 'name', self.gf(
            'django.db.models.fields.SlugField')(max_length=50, unique=True))

    models = {
        u'datasets.datagroup': {
            'Meta': {'object_name': 'DataGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'datasets.dataset': {
            'Meta': {'unique_together': "([u'data_group', u'data_type'],)", 'object_name': 'DataSet'},
            'auto_ids': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bearer_token': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'capped_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'data_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataGroup']", 'on_delete': 'models.PROTECT'}),
            'data_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataType']", 'on_delete': 'models.PROTECT'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_age_expected': ('django.db.models.fields.PositiveIntegerField', [], {'default': '86400', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'queryable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'raw_queries_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'realtime': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'upload_filters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'upload_format': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'datasets.datatype': {
            'Meta': {'object_name': 'DataType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['datasets']

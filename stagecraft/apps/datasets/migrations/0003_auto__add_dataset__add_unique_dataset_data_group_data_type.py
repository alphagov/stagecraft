# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DataSet'
        db.create_table(u'datasets_dataset', (
            (u'id', self.gf('django.db.models.fields.AutoField')
             (primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')
             (unique=True, max_length=50)),
            ('data_group', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['datasets.DataGroup'])),
            ('data_type', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['datasets.DataType'])),
            ('raw_queries_allowed', self.gf(
                'django.db.models.fields.BooleanField')(default=True)),
            ('bearer_token', self.gf('django.db.models.fields.CharField')
             (max_length=255, blank=True)),
            ('upload_format', self.gf('django.db.models.fields.CharField')
             (max_length=255, blank=True)),
            ('upload_filters', self.gf(
                'django.db.models.fields.TextField')(blank=True)),
            ('auto_ids', self.gf(
                'django.db.models.fields.TextField')(blank=True)),
            ('queryable', self.gf(
                'django.db.models.fields.BooleanField')(default=True)),
            ('realtime', self.gf(
                'django.db.models.fields.BooleanField')(default=False)),
            ('capped_size', self.gf('django.db.models.fields.PositiveIntegerField')(
                default=None, null=True, blank=True)),
            ('max_age_expected', self.gf('django.db.models.fields.PositiveIntegerField')(
                default=86400, null=True, blank=True)),
        ))
        db.send_create_signal(u'datasets', ['DataSet'])

        # Adding unique constraint on 'DataSet', fields ['data_group',
        # 'data_type']
        db.create_unique(
            u'datasets_dataset', ['data_group_id', 'data_type_id'])

    def backwards(self, orm):
        # Removing unique constraint on 'DataSet', fields ['data_group',
        # 'data_type']
        db.delete_unique(
            u'datasets_dataset', ['data_group_id', 'data_type_id'])

        # Deleting model 'DataSet'
        db.delete_table(u'datasets_dataset')

    models = {
        u'datasets.datagroup': {
            'Meta': {'object_name': 'DataGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'datasets.dataset': {
            'Meta': {'unique_together': "([u'data_group', u'data_type'],)", 'object_name': 'DataSet'},
            'auto_ids': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bearer_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'capped_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'data_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataGroup']"}),
            'data_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_age_expected': ('django.db.models.fields.PositiveIntegerField', [], {'default': '86400', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
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

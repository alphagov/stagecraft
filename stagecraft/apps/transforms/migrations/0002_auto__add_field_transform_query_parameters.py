# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Transform.query_parameters'
        db.add_column(u'transforms_transform', 'query_parameters',
                      self.gf('jsonfield.fields.JSONField')(default='', blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Transform.query_parameters'
        db.delete_column(u'transforms_transform', 'query_parameters')


    models = {
        u'datasets.datagroup': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'datasets.datatype': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataType'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'transforms.transform': {
            'Meta': {'object_name': 'Transform'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'input_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['datasets.DataGroup']"}),
            'input_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['datasets.DataType']"}),
            'options': ('jsonfield.fields.JSONField', [], {'blank': 'True'}),
            'output_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['datasets.DataGroup']"}),
            'output_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['datasets.DataType']"}),
            'query_parameters': ('jsonfield.fields.JSONField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['transforms.TransformType']"})
        },
        u'transforms.transformtype': {
            'Meta': {'object_name': 'TransformType'},
            'function': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'schema': ('jsonfield.fields.JSONField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['transforms']
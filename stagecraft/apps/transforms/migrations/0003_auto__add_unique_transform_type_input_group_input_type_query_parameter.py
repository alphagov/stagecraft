# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'Transform', fields ['type', 'input_group', 'input_type', 'query_parameters', 'options', 'output_group', 'output_type']
        db.create_unique(u'transforms_transform', ['type_id', 'input_group_id', 'input_type_id', 'query_parameters', 'options', 'output_group_id', 'output_type_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Transform', fields ['type', 'input_group', 'input_type', 'query_parameters', 'options', 'output_group', 'output_type']
        db.delete_unique(u'transforms_transform', ['type_id', 'input_group_id', 'input_type_id', 'query_parameters', 'options', 'output_group_id', 'output_type_id'])


    models = {
        u'datasets.datagroup': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'datasets.datatype': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'DataType'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'transforms.transform': {
            'Meta': {'unique_together': "(('type', 'input_group', 'input_type', 'query_parameters', 'options', 'output_group', 'output_type'),)", 'object_name': 'Transform'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'input_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['datasets.DataGroup']"}),
            'input_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['datasets.DataType']"}),
            'options': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'output_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['datasets.DataGroup']"}),
            'output_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['datasets.DataType']"}),
            'query_parameters': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['transforms.TransformType']"})
        },
        u'transforms.transformtype': {
            'Meta': {'object_name': 'TransformType'},
            'function': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'schema': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'})
        }
    }

    complete_apps = ['transforms']
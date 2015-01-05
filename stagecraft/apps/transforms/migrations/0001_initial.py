# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TransformType'
        db.create_table(u'transforms_transformtype', (
            ('id', self.gf('uuidfield.fields.UUIDField')
             (unique=True, max_length=32, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')
             (unique=True, max_length=25)),
            ('schema', self.gf('jsonfield.fields.JSONField')(blank=True)),
            ('function', self.gf('django.db.models.fields.CharField')
             (unique=True, max_length=200)),
        ))
        db.send_create_signal(u'transforms', ['TransformType'])

        # Adding model 'Transform'
        db.create_table(u'transforms_transform', (
            ('id', self.gf('uuidfield.fields.UUIDField')
             (unique=True, max_length=32, primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')
             (to=orm['transforms.TransformType'])),
            ('input_group', self.gf('django.db.models.fields.related.ForeignKey')(
                blank=True, related_name='+', null=True, to=orm['datasets.DataGroup'])),
            ('input_type', self.gf('django.db.models.fields.related.ForeignKey')(
                related_name='+', to=orm['datasets.DataType'])),
            ('options', self.gf('jsonfield.fields.JSONField')(blank=True)),
            ('output_group', self.gf('django.db.models.fields.related.ForeignKey')(
                blank=True, related_name='+', null=True, to=orm['datasets.DataGroup'])),
            ('output_type', self.gf('django.db.models.fields.related.ForeignKey')(
                related_name='+', to=orm['datasets.DataType'])),
        ))
        db.send_create_signal(u'transforms', ['Transform'])

    def backwards(self, orm):
        # Deleting model 'TransformType'
        db.delete_table(u'transforms_transformtype')

        # Deleting model 'Transform'
        db.delete_table(u'transforms_transform')

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

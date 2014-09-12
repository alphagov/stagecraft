# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Module.order'
        db.add_column(u'dashboards_module', 'order',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Module.order'
        db.delete_column(u'dashboards_module', 'order')


    models = {
        'dashboards.dashboard': {
            'Meta': {'object_name': 'Dashboard'},
            'business_model': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '31', 'blank': 'True'}),
            'costs': ('django.db.models.fields.CharField', [], {'max_length': '1500', 'blank': 'True'}),
            'customer_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'dashboard_type': ('django.db.models.fields.CharField', [], {'default': "'transaction'", 'max_length': '30'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'description_extra': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'improve_dashboard_message': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Node']", 'null': 'True', 'blank': 'True'}),
            'other_notes': ('django.db.models.fields.CharField', [], {'max_length': '700', 'blank': 'True'}),
            'page_type': ('django.db.models.fields.CharField', [], {'default': "'dashboard'", 'max_length': '80'}),
            'published': ('django.db.models.fields.BooleanField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '90'}),
            'strapline': ('django.db.models.fields.CharField', [], {'default': "'Dashboard'", 'max_length': '40'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        'dashboards.link': {
            'Meta': {'object_name': 'Link'},
            'dashboard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dashboards.Dashboard']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'link_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'dashboards.module': {
            'Meta': {'unique_together': "(('dashboard', 'slug'),)", 'object_name': 'Module'},
            'dashboard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dashboards.Dashboard']"}),
            'data_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataSet']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'info': ('dbarray.fields.TextArrayField', [], {}),
            'options': ('jsonfield.fields.JSONField', [], {}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'query_parameters': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dashboards.ModuleType']"})
        },
        'dashboards.moduletype': {
            'Meta': {'object_name': 'ModuleType'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'schema': ('jsonfield.fields.JSONField', [], {})
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
        },
        u'organisation.node': {
            'Meta': {'object_name': 'Node'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['organisation.Node']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'typeOf': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.NodeType']"})
        },
        u'organisation.nodetype': {
            'Meta': {'object_name': 'NodeType'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        }
    }

    complete_apps = ['dashboards']
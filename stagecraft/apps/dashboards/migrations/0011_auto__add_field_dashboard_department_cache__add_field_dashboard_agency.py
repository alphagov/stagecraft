# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Dashboard.department_cache'
        db.add_column(u'dashboards_dashboard', 'department_cache',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='dashboards_owned_by_department', null=True, to=orm['organisation.Node']),
                      keep_default=False)

        # Adding field 'Dashboard.agency_cache'
        db.add_column(u'dashboards_dashboard', 'agency_cache',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='dashboards_owned_by_agency', null=True, to=orm['organisation.Node']),
                      keep_default=False)

        # Adding field 'Dashboard.service_cache'
        db.add_column(u'dashboards_dashboard', 'service_cache',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='dashboards_owned_by_service', null=True, to=orm['organisation.Node']),
                      keep_default=False)

        # Adding field 'Dashboard.transaction_cache'
        db.add_column(u'dashboards_dashboard', 'transaction_cache',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='dashboards_owned_by_transaction', null=True, to=orm['organisation.Node']),
                      keep_default=False)

        # Changing field 'Dashboard.title'
        db.alter_column(u'dashboards_dashboard', 'title', self.gf('django.db.models.fields.CharField')(max_length=256))

    def backwards(self, orm):
        # Deleting field 'Dashboard.department_cache'
        db.delete_column(u'dashboards_dashboard', 'department_cache_id')

        # Deleting field 'Dashboard.agency_cache'
        db.delete_column(u'dashboards_dashboard', 'agency_cache_id')

        # Deleting field 'Dashboard.service_cache'
        db.delete_column(u'dashboards_dashboard', 'service_cache_id')

        # Deleting field 'Dashboard.transaction_cache'
        db.delete_column(u'dashboards_dashboard', 'transaction_cache_id')

        # Changing field 'Dashboard.title'
        db.alter_column(u'dashboards_dashboard', 'title', self.gf('django.db.models.fields.CharField')(max_length=80))

    models = {
        'dashboards.dashboard': {
            'Meta': {'object_name': 'Dashboard'},
            'agency_cache': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'dashboards_owned_by_agency'", 'null': 'True', 'to': u"orm['organisation.Node']"}),
            'business_model': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '31', 'blank': 'True'}),
            'costs': ('django.db.models.fields.CharField', [], {'max_length': '1500', 'blank': 'True'}),
            'customer_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'dashboard_type': ('django.db.models.fields.CharField', [], {'default': "'transaction'", 'max_length': '30'}),
            'department_cache': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'dashboards_owned_by_department'", 'null': 'True', 'to': u"orm['organisation.Node']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'description_extra': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'improve_dashboard_message': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Node']", 'null': 'True', 'blank': 'True'}),
            'other_notes': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'page_type': ('django.db.models.fields.CharField', [], {'default': "'dashboard'", 'max_length': '80'}),
            'published': ('django.db.models.fields.BooleanField', [], {}),
            'service_cache': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'dashboards_owned_by_service'", 'null': 'True', 'to': u"orm['organisation.Node']"}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '90'}),
            'strapline': ('django.db.models.fields.CharField', [], {'default': "'Dashboard'", 'max_length': '40'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'transaction_cache': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'dashboards_owned_by_transaction'", 'null': 'True', 'to': u"orm['organisation.Node']"})
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
            'data_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['datasets.DataSet']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'info': ('dbarray.fields.TextArrayField', [], {'blank': 'True'}),
            'options': ('jsonfield.fields.JSONField', [], {'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dashboards.Module']", 'null': 'True', 'blank': 'True'}),
            'query_parameters': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
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
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '60'})
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
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200', 'blank': 'True'}),
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
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'organisation.node': {
            'Meta': {'object_name': 'Node'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['organisation.Node']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '90'}),
            'typeOf': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.NodeType']"})
        },
        u'organisation.nodetype': {
            'Meta': {'object_name': 'NodeType'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        }
    }

    complete_apps = ['dashboards']

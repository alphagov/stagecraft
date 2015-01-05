# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("organisation", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding model 'Dashboard'
        db.create_table(u'dashboards_dashboard', (
            ('id', self.gf('uuidfield.fields.UUIDField')
             (unique=True, max_length=32, primary_key=True)),
            ('slug', self.gf('django.db.models.fields.CharField')
             (unique=True, max_length=90)),
            ('dashboard_type', self.gf('django.db.models.fields.CharField')
             (default='transaction', max_length=30)),
            ('page_type', self.gf('django.db.models.fields.CharField')
             (default='dashboard', max_length=80)),
            ('published', self.gf('django.db.models.fields.BooleanField')()),
            ('title', self.gf('django.db.models.fields.CharField')
             (max_length=80)),
            ('description', self.gf('django.db.models.fields.CharField')
             (max_length=500, blank=True)),
            ('description_extra', self.gf('django.db.models.fields.CharField')
             (max_length=400, blank=True)),
            ('costs', self.gf('django.db.models.fields.CharField')
             (max_length=1500, blank=True)),
            ('other_notes', self.gf('django.db.models.fields.CharField')
             (max_length=700, blank=True)),
            ('customer_type', self.gf('django.db.models.fields.CharField')
             (default='', max_length=20, blank=True)),
            ('business_model', self.gf('django.db.models.fields.CharField')
             (default='', max_length=20, blank=True)),
            ('improve_dashboard_message', self.gf(
                'django.db.models.fields.BooleanField')(default=True)),
            ('strapline', self.gf('django.db.models.fields.CharField')
             (default='Dashboard', max_length=40)),
            ('tagline', self.gf('django.db.models.fields.CharField')
             (max_length=400, blank=True)),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['organisation.Node'], null=True, blank=True)),
        ))
        db.send_create_signal('dashboards', ['Dashboard'])

        # Adding model 'Link'
        db.create_table(u'dashboards_link', (
            ('id', self.gf('uuidfield.fields.UUIDField')
             (unique=True, max_length=32, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')
             (max_length=100)),
            ('url', self.gf('django.db.models.fields.URLField')
             (max_length=200)),
            ('dashboard', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['dashboards.Dashboard'])),
            ('link_type', self.gf(
                'django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('dashboards', ['Link'])

        # Adding model 'ModuleType'
        db.create_table(u'dashboards_moduletype', (
            ('id', self.gf('uuidfield.fields.UUIDField')
             (unique=True, max_length=32, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')
             (unique=True, max_length=25)),
            ('schema', self.gf('jsonfield.fields.JSONField')()),
        ))
        db.send_create_signal('dashboards', ['ModuleType'])

        # Adding model 'Module'
        db.create_table(u'dashboards_module', (
            ('id', self.gf('uuidfield.fields.UUIDField')
             (unique=True, max_length=32, primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')
             (to=orm['dashboards.ModuleType'])),
            ('dashboard', self.gf('django.db.models.fields.related.ForeignKey')(
                to=orm['dashboards.Dashboard'])),
            ('slug', self.gf('django.db.models.fields.CharField')
             (max_length=60)),
            ('title', self.gf('django.db.models.fields.CharField')
             (max_length=60)),
            ('description', self.gf(
                'django.db.models.fields.CharField')(max_length=200)),
            ('info', self.gf('dbarray.fields.CharArrayField')(max_length=255)),
            ('options', self.gf('jsonfield.fields.JSONField')()),
        ))
        db.send_create_signal('dashboards', ['Module'])

        # Adding unique constraint on 'Module', fields ['dashboard', 'slug']
        db.create_unique(u'dashboards_module', ['dashboard_id', 'slug'])

    def backwards(self, orm):
        # Removing unique constraint on 'Module', fields ['dashboard', 'slug']
        db.delete_unique(u'dashboards_module', ['dashboard_id', 'slug'])

        # Deleting model 'Dashboard'
        db.delete_table(u'dashboards_dashboard')

        # Deleting model 'Link'
        db.delete_table(u'dashboards_link')

        # Deleting model 'ModuleType'
        db.delete_table(u'dashboards_moduletype')

        # Deleting model 'Module'
        db.delete_table(u'dashboards_module')

    models = {
        'dashboards.dashboard': {
            'Meta': {'object_name': 'Dashboard'},
            'business_model': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
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
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'info': ('dbarray.fields.CharArrayField', [], {'max_length': '255'}),
            'options': ('jsonfield.fields.JSONField', [], {}),
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

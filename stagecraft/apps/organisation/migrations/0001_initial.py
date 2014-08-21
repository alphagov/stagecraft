# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'NodeType'
        db.create_table(u'organisation_nodetype', (
            ('id', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=32, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
        ))
        db.send_create_signal(u'organisation', ['NodeType'])

        # Adding model 'Node'
        db.create_table(u'organisation_node', (
            ('id', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=32, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('typeOf', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.NodeType'])),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='children', null=True, to=orm['organisation.Node'])),
            (u'lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal(u'organisation', ['Node'])


    def backwards(self, orm):
        # Deleting model 'NodeType'
        db.delete_table(u'organisation_nodetype')

        # Deleting model 'Node'
        db.delete_table(u'organisation_node')


    models = {
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

    complete_apps = ['organisation']
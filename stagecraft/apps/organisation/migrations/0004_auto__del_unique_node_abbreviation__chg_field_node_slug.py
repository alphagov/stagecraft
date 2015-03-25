# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Node', fields ['abbreviation']
        db.delete_unique(u'organisation_node', ['abbreviation'])


        # Changing field 'Node.slug'
        db.alter_column(u'organisation_node', 'slug', self.gf('django.db.models.fields.CharField')(max_length=150))

    def backwards(self, orm):
        # Adding unique constraint on 'Node', fields ['abbreviation']
        db.create_unique(u'organisation_node', ['abbreviation'])


        # Changing field 'Node.slug'
        db.alter_column(u'organisation_node', 'slug', self.gf('django.db.models.fields.CharField')(max_length=90, null=True))

    models = {
        u'organisation.node': {
            'Meta': {'object_name': 'Node'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['organisation.Node']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '150'}),
            'typeOf': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.NodeType']"})
        },
        u'organisation.nodetype': {
            'Meta': {'object_name': 'NodeType'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        }
    }

    complete_apps = ['organisation']
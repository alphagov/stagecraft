# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        def produce_tuple(n):
            return (n.id, n.parent.id if n.parent is not None else None)

        # build list of relations
        relationships = [
            produce_tuple(n) for n in orm['organisation.Node'].objects.all()]

        # Adding M2M table for field parents on 'Node'
        m2m_table_name = db.shorten_name(u'organisation_node_parents')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(
                verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_node', models.ForeignKey(
                orm[u'organisation.node'], null=False)),
            ('to_node', models.ForeignKey(
                orm[u'organisation.node'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_node_id', 'to_node_id'])

        for from_id, to_id in relationships:
            if to_id is not None:
                db.execute('''
                INSERT INTO ''' + m2m_table_name + ''' (from_node_id, to_node_id)
                VALUES (%s, %s)
                ''', [from_id, to_id])

        # Deleting field 'Node.lft'
        db.delete_column(u'organisation_node', u'lft')

        # Deleting field 'Node.parent'
        db.delete_column(u'organisation_node', 'parent_id')

        # Deleting field 'Node.level'
        db.delete_column(u'organisation_node', u'level')

        # Deleting field 'Node.tree_id'
        db.delete_column(u'organisation_node', u'tree_id')

        # Deleting field 'Node.rght'
        db.delete_column(u'organisation_node', u'rght')

    def backwards(self, orm):
        raise RuntimeError(
            "Cannot reverse this migration.")

    models = {
        u'organisation.node': {
            'Meta': {'object_name': 'Node'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['organisation.Node']"}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['organisation.Node']", 'symmetrical': 'False'}),
            'typeOf': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.NodeType']"})
        },
        u'organisation.nodetype': {
            'Meta': {'object_name': 'NodeType'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        }
    }

    complete_apps = ['organisation']

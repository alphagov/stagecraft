# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        user_datasets = db.execute(
            'select * from users_user_data_sets')

        for ds in user_datasets:
            db.execute("INSERT INTO datasets_dataset_owners (dataset_id, user_id) VALUES (%s, %s)", [ds[2], ds[1]])

    def backwards(self, orm):
        db.clear_table('datasets_dataset_owners')

    models = {
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
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['users.User']", 'symmetrical': 'False'}),
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
        u'datasets.oauthuser': {
            'Meta': {'object_name': 'OAuthUser'},
            'access_token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'expires_at': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permissions': ('dbarray.fields.CharArrayField', [], {'max_length': '255'}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'users.user': {
            'Meta': {'ordering': "[u'email']", 'object_name': 'User'},
            'data_sets': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['datasets.DataSet']", 'symmetrical': 'False', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '254'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['datasets']
    symmetrical = True

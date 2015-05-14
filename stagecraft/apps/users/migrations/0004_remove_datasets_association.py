# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("datasets", "0019_copy_user_datasets"),
    )

    def forwards(self, orm):
        # Removing M2M table for field data_sets on 'User'
        db.delete_table(db.shorten_name(u'users_user_data_sets'))


    def backwards(self, orm):
        # Adding M2M table for field data_sets on 'User'
        m2m_table_name = db.shorten_name(u'users_user_data_sets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm[u'users.user'], null=False)),
            ('dataset', models.ForeignKey(orm[u'datasets.dataset'], null=False))
        ))
        db.create_unique(m2m_table_name, ['user_id', 'dataset_id'])


    models = {
        u'users.user': {
            'Meta': {'ordering': "[u'email']", 'object_name': 'User'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '254'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['users']

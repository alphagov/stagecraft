# -*- coding: utf-8 -*-
# from south.db import db
# from south.v2 import DataMigration
# from django.db import models
# from django.db.models import Q
from __future__ import unicode_literals

import pprint as pp
import json
from performanceplatform.client import DataSet as client

base_url = 'https://www.performance.service.gov.uk'

input_sets = [
    'carers_allowance_monthly_claims',
    'carers_allowance_weekly_claims'
]

output_sets = 'carers_allowance_transactions_by_channel'

key_mapping = {
    "key": "channel",
    "value": "count"
}

value_mapping = {

}


def get_data_from_claims_sets():
    input_data = []
    for set_name in input_sets:
        data_set = client.from_name(base_url, set_name)
        for item in data_set.get().json()['data']:
            input_data.append(item)
    return input_data


def apply_new_key_mappings(documents):
    docs = []
    for document in documents:
        for key, val in document.items():
            if key in key_mapping:
                document.pop(key)
                document[key_mapping[key]] = val
            else:
                document[key] = val
        docs.append(document)
    return docs


def unique_vals(docs):
    for doc in docs:
        pp.pprint(doc['channel'])
    return set([doc['channel']] for doc in docs)


input_sets_data = get_data_from_claims_sets()
new = apply_new_key_mappings(input_sets_data)
pp.pprint(len(input_sets_data))
pp.pprint(len(new))
pp.pprint(new[0])

# unique_vals(new)
# pp.pprint(apply_new_key_mappings(input_sets_data))


class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName".
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'datasets.backdropuser': {
            'Meta': {'ordering': "[u'email']", 'object_name': 'BackdropUser'},
            'data_sets': (
                'django.db.models.fields.related.ManyToManyField',
                [],
                {
                    'to': u"orm['datasets.DataSet']",
                    'symmetrical': 'False',
                    'blank': 'True'
                }
            ),
            'email': (
                'django.db.models.fields.EmailField',
                [],
                {
                    'unique': 'True',
                    'max_length': '254'
                }
            ),
            u'id': (
                'django.db.models.fields.AutoField',
                [],
                {
                    'primary_key': 'True'
                }
            )
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
        }
    }

    complete_apps = ['datasets']
    symmetrical = True

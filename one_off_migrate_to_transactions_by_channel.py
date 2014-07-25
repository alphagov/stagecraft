#!/usr/bin/env python
# encoding: utf-8
from stagecraft.libs.mass_update import migrate_data_set
from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType
import sys

transaction_by_channel_data_set_mappings = [
    {
        'old_data_set': {
            'data_group': "carers-allowance",
            'data_type': "weekly-claims"
        },
        'new_data_set': {
            'auto_ids': '_timestamp,channel',
            'data_group': "carers-allowance",
            'data_type': "transactions-by-channel"
        },
        'data_mapping': {
            'key_mapping': {
                "key": "channel",
                "value": "count"
            },
            'value_mapping': {
                "ca_clerical_received": "paper",
                "ca_e_claims_received": "digital"
            }
        }
    },
    {
        'old_data_set': {
            'data_group': "lasting-power-of-attorney",
            'data_type': "volumes"
        },
        'new_data_set': {
            'data_group': "lasting-power-of-attorney",
            'data_type': "transactions-by-channel",
            'auto_ids': "_timestamp,channel",
        },
        'data_mapping': {
            'key_mapping': {
                "key": "channel",
                "value": "count"
            },
            'value_mapping': {
            }
        }
    }
]


def run():
    for mapping in transaction_by_channel_data_set_mappings:
        print "converting {} to {}".format(
            mapping['old_data_set'],
            mapping['new_data_set'])
        print "this will not delete the old data set"
        migrate_data_set(mapping['old_data_set'],
                         mapping['new_data_set'],
                         mapping["data_mapping"])


def undo():
    for mapping in transaction_by_channel_data_set_mappings:
        data_type = DataType.objects.get(
            name=mapping['new_data_set']['data_group'])
        data_group = DataGroup.objects.get(
            name=mapping['new_data_set']['data_type'])
        DataSet.objects.get(
            data_group=data_group,
            data_type=data_type
        ).delete()


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'run':
        run()
    elif len(sys.argv) == 2 and sys.argv[1] == 'undo':
        undo()
    else:
        print(
            "Usage: ./one_off_migrate_to_transactions_by_channel.py run/undo")
        sys.exit(2)

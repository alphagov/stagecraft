import os
import json
import requests
from fnmatch import filter as fnfilter
import pprint
import sys

# For this script to work correctly, you need to run
# pip install git+https://github.com/jirikuncar/dictdiffer@no-empty-lists


def spotlight_json(path):
    for root, dirnames, filenames in os.walk(path):
        for filename in fnfilter(filenames, '*.json'):
            with open(os.path.join(root, filename)) as jsonfile:
                yield (filename, json.loads(jsonfile.read()))

stagecraft_url = 'http://stagecraft.development.performance.service.gov.uk'

if len(sys.argv) == 2:
    path = sys.argv[1]
else:
    print('Please specify a path containing the spotlight json files')
    path = os.path.join(
        os.path.dirname(__file__),
        '../spotlight/app/support/stagecraft_stub/responses')
for filename, old_json in spotlight_json(path):
    if not isinstance(old_json, dict):
        print 'skipping {}'.format(filename)
        continue
    skip_dashboards = [
        'housing', 'dashboards', 'no-realistic-dashboard',
        'unimplemented-page-type'
    ]
    if filename in ['{}.json'.format(name) for name in skip_dashboards]:
        print 'skipping {}'.format(filename)
        continue

    for fieldname in ['business-model', 'customer-type', 'description',
                      'description-extra', 'costs', 'other-notes',
                      'tagline']:
        old_json.setdefault(fieldname, '')
    old_json.setdefault('relatedPages', {}).setdefault('other', [])
    old_json.setdefault('relatedPages', {}).setdefault(
        'improve-dashboard-message', False)

    new_json = requests.get(
        stagecraft_url + '/public/dashboards?slug={}'.format(
            old_json['slug']
        )).json()
    oldmodules = {}
    for module in old_json['modules']:
        module.setdefault('description', '')
        module.setdefault('info', [])
        oldmodules[module['slug']] = module

    if old_json != new_json:
        print '{} differs'.format(filename)
        pprint.pprint(old_json)
        pprint.pprint(new_json)

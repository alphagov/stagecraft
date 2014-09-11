import os
import json
import requests
from dictdiffer import diff
from glob import glob
from fnmatch import filter as fnfilter
import pprint

# For this script to work correctly, you need to run
# pip install git+https://github.com/jirikuncar/dictdiffer@no-empty-lists


def spotlight_json(path):
    for root, dirnames, filenames in os.walk(path):
        for filename in fnfilter(filenames, '*.json'):
            with open(os.path.join(root, filename)) as jsonfile:
                yield (filename, json.loads(jsonfile.read()))

stagecraft_url = 'http://stagecraft.development.performance.service.gov.uk'

path = os.path.join(
    os.path.dirname(__file__),
    '../../spotlight/app/support/stagecraft_stub/responses/')

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
        # module.setdefault('data-source', {}).setdefault('query-params', {})
        oldmodules[module['slug']] = module

    module_diffs = {}
    # for module in new_json['modules']:
    #     if module['slug'] in oldmodules:
    #         oldmodule = oldmodules[module['slug']]
    #         module_diff = list(diff(oldmodule, module))
    #         if len(module_diff) > 0:
    #             module_diffs[module['slug']] = module_diff
    #     else:
    #         print 'missing module {} for {}'.format(module['slug'], filename)

    # try:
    #     del(old_json['modules'])
    #     del(new_json['modules'])
    # except KeyError:
    #     pass

    diffs = list(diff(old_json, new_json))
    if len(diffs) != 0:
        print '{} differs'.format(filename)
        pprint.pprint(diffs)
    if len(module_diffs) != 0:
        print '{} differs'.format(filename)
        for module, module_diff in module_diffs.iteritems():
            print '{} differs'.format(module)
            pprint.pprint(module_diff)

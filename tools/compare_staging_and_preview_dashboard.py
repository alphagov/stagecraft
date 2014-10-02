import os
import json
import requests
from dictdiffer import diff
from fnmatch import filter as fnfilter
import pprint
import sys

# For this script to work correctly, you need to run
# pip install git+https://github.com/jirikuncar/dictdiffer@no-empty-lists


stagecraft_url = 'https://stagecraft.{}.performance.service.gov.uk'
preview_url = stagecraft_url.format('preview')
staging_url = stagecraft_url.format('staging')

if len(sys.argv) == 2:
    slug = sys.argv[1]
else:
    pass

preview_json = requests.get(
    preview_url +
    '/public/dashboards?slug={}'.format(
        slug)).json()
staging_json = requests.get(
    staging_url +
    '/public/dashboards?slug={}'.format(
        slug)).json()

# for fieldname in ['business-model', 'customer-type', 'description',
#                     'description-extra', 'costs', 'other-notes',
#                     'tagline']:
#     old_json.setdefault(fieldname, '')
# old_json.setdefault('relatedPages', {}).setdefault('other', [])
# old_json.setdefault('relatedPages', {}).setdefault(
#     'improve-dashboard-message', False)

# oldmodules = {}
# for module in old_json['modules']:
#     module.setdefault('description', '')
#     module.setdefault('info', [])
#     oldmodules[module['slug']] = module

diffs = list(diff(preview_json, staging_json))
if len(diffs) != 0:
    pprint.pprint(diffs)

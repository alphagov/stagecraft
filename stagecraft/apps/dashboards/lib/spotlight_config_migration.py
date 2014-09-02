from glob import glob
from fnmatch import filter as fnfilter
import os
import json
from mock import patch
import requests


def spotlight_json(path):
    for root, dirnames, filenames in os.walk(path):
        for filename in fnfilter(filenames, '*.json'):
            with open(os.path.join(root, filename)) as jsonfile:
                yield json.loads(jsonfile.read())




class Dashboard():

    def __init__(self, url):
        self.url = url

    def set_data(self, data):
        self.data = data

    # send to stagecraft
    def send(self):
        if 'organisation' in self.data:
            resp = requests.get(
                self.url + "/organisation/" + self.data['organisation'])
            if resp.status_code != 200:
                # create the org, this is a migration
                raise ValueError('Must use a valid org')

        requests.post(self.url + "/dashboard/", self.data)
# stub to use when unit testing
# with patch('__main__.spotlight_json') as mock:
#     mock.return_value = ['a']
#     for i in spotlight_json():
#         print i

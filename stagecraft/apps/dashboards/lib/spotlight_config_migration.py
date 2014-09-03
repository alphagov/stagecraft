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

    def set_data(self, **kwargs):
        self.data = kwargs

    def create_organisation(self, organisation_type):
            resp = requests.get(
                self.url + "/organisation/node",
                params={
                    "name": self.data[organisation_type]["title"],
                    "abbreviation": self.data[organisation_type]['abbr']
                }
            )
            if resp.status_code == 404:
                requests.post(self.url + "/organisation/node", {
                    "name": self.data[organisation_type]["title"],
                    "abbreviation": self.data[organisation_type]["abbr"],
                    "type_id": resp.json()["type_id"]
                }
                )
            self.data.pop(organisation_type)

    # send to stagecraft
    def send(self):
        if 'department' in self.data:
            self.create_organisation('department')
        if 'agency' in self.data:
            self.create_organisation('agency')
        requests.post(self.url + "/dashboard/", self.data)
# stub to use when unit testing
# with patch('__main__.spotlight_json') as mock:
#         print i

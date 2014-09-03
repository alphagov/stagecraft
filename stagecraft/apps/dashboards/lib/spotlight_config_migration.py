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

    def build_organisation_data(self):
        return {
            "name": self.data["department"]["title"],
            "abbreviation": self.data["department"]["abbr"]
        }

    def create_organisation(self, organisation_type, parent_id=None):
            resp = requests.get(
                self.url + "/organisation/node",
                params={
                    "name": self.data[organisation_type]["title"],
                    "abbreviation": self.data[organisation_type]['abbr']
                }
            )
            if resp.status_code == 404:
                post_data = {
                    "name": self.data[organisation_type]["title"],
                    "abbreviation": self.data[organisation_type]["abbr"],
                    "type_id": resp.json()["type_id"]
                }
                if parent_id:
                    post_data['parent_id'] = parent_id
                post_resp = requests.post(
                    self.url + "/organisation/node", post_data
                )
                org_id = post_resp.json()['id']
            else:
                org_id = resp.json()['id']
            self.data.pop(organisation_type)
            return org_id

    # send to stagecraft
    def send(self):
        department_id = None
        agency_id = None
        if 'department' in self.data:
            department_id = self.create_organisation('department')
        if 'agency' in self.data:
            agency_id = self.create_organisation('agency', parent_id=department_id)
        if agency_id and department_id:
            self.data["organisation"] = agency_id
        elif department_id:
            self.data["organisation"] = department_id
        requests.post(self.url + "/dashboard/", self.data)
# stub to use when unit testing
# with patch('__main__.spotlight_json') as mock:
#         print i

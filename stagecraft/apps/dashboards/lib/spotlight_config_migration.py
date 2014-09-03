from glob import glob
from fnmatch import filter as fnfilter
import os
import json
from mock import patch
import requests
import logging


def spotlight_json(path):
    for root, dirnames, filenames in os.walk(path):
        for filename in fnfilter(filenames, '*.json'):
            with open(os.path.join(root, filename)) as jsonfile:
                yield json.loads(jsonfile.read())




class Dashboard():

    def __init__(self, url):
        self.url = url
        self.type_id_map = {}

    def set_data(self, **kwargs):
        self.data = kwargs

    def build_organisation_data(self):
        return {
            "name": self.data["department"]["title"],
            "abbreviation": self.data["department"]["abbr"]
        }

    def get_type_id(self, type_str):
        if type_str not in self.type_id_map:
            type_request = requests.get(
                self.url + "/organisation/type",
                params={"name": type}
            )
            if len(type_request.json()) == 1:
                self.type_id_map[type_str] = type_request.json()['id']
            else:
                logging.getLogger(__name__).info('Unknown type {} for dashboard {}, creating'.format(
                    type_str, self.data['slug']))
                post_request = requests.post(
                    self.url + "/organisation/type",
                    {"name" :type_str}
                )
                self.type_id_map[type_str] = post_request.json()['id']

        return self.type_id_map[type_str]

    def create_organisation(self, organisation_type, parent_id=None):
            resp = requests.get(
                self.url + "/organisation/node",
                params={
                    "name": self.data[organisation_type]["title"],
                    "abbreviation": self.data[organisation_type]['abbr']
                }
            )
            print resp.content
            if resp.status_code == 200 and len(resp.json()) == 0:
                post_data = {
                    "name": self.data[organisation_type]["title"],
                    "abbreviation": self.data[organisation_type]["abbr"],
                    "type_id": self.get_type_id(organisation_type)
                }
                if parent_id:
                    post_data['parent_id'] = parent_id
                post_resp = requests.post(
                    self.url + "/organisation/node", post_data
                )
                org_id = post_resp.json()[0]['id']
            elif len(response.json()) > 1:
                logger.warning(
                    'multiple organisations found for dashboard{}'.format(
                        self.data['slug']
                    ))
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

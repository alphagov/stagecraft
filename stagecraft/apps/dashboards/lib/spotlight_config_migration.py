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
                yield (filename, json.loads(jsonfile.read()))


logger = logging.getLogger(__name__)


class Dashboard():

    def __init__(self, url):
        self.url = url
        self.type_id_map = {}
        self.stagecraft_client = StagecraftClient(url)
        self.logger = logging.getLogger(__name__)

    def set_data(self, **kwargs):
        self.data = kwargs

    def get_type_id(self, type_str):
        if type_str not in self.type_id_map:
            type_request = self.stagecraft_client.get_organisation_type(
                type_str)
            if len(type_request.json()) == 1:
                self.type_id_map[type_str] = type_request.json().pop()['id']
            else:
                logger.info(
                    'Unknown type {} for dashboard {}, creating'.format(
                        type_str, self.data['slug']))
                post_response = (
                    self.stagecraft_client.create_organisation_type(type_str)
                )
                self.type_id_map[type_str] = post_response.json()['id']

        return self.type_id_map[type_str]

    def create_organisation(self, organisation_type, parent_id=None):
            resp = self.stagecraft_client.get_organisation(
                self.data[organisation_type]['title'],
                self.data[organisation_type].get('abbr', None)
            )
            assert resp.status_code == 200

            if len(resp.json()) == 0:
                post_data = {
                    "name": self.data[organisation_type]["title"],
                    "type_id": self.get_type_id(organisation_type)
                }
                if "abbr" in self.data[organisation_type]:
                    post_data["abbreviation"] = (
                        self.data[organisation_type]["abbr"]
                    )
                if parent_id:
                    post_data['parent_id'] = parent_id
                post_resp = self.stagecraft_client.create_organisation(
                    post_data)
                self.logger.debug(
                    'response from creating org type {} - {}'.format(
                        organisation_type, post_resp.json()))
                org_id = post_resp.json()['id']
            elif len(resp.json()) > 1:
                self.logger.warning(
                    'multiple organisations found for dashboard{}'.format(
                        self.data['slug']
                    ))
                org_id = resp.json()[0]['id']
            else:
                org_id = resp.json()[0]['id']
            self.data.pop(organisation_type)
            return org_id

    # send to stagecraft
    def send(self):
        department_id = None
        agency_id = None
        if 'department' in self.data:
            department_id = self.create_organisation('department')
        if 'agency' in self.data:
            agency_id = self.create_organisation(
                'agency', parent_id=department_id)
        if agency_id and department_id:
            self.data["organisation"] = agency_id
        elif department_id:
            self.data["organisation"] = department_id
        dashboard_response = self.stagecraft_client.create_dashboard(self.data)
        self.create_modules(dashboard_response.json()['id'])

    def create_modules(self, dashboard_id):
        for module in self.data['modules']:
            module_type_id = self.get_module_type_id(module['module-type'])
            options = self.get_options_for_module(module)
            logger.debug(module['slug'])
            self.stagecraft_client.add_module_to_dashboard(
                dashboard_id,
                {
                    'type_id': module_type_id,
                    'slug': module['slug'],
                    'title': module['title'],
                    'description': module.get('description', ''),
                    'info': module.get('info', []),
                    'options': options,
                })

    def get_options_for_module(self, module):
        keys_to_remove = [
            'slug', 'module-type', 'title', 'description', 'info',
            'data-source'
        ]
        return {k: v for k, v in module.items() if k not in keys_to_remove}

    def get_module_type_id(self, module_type):
        get_response = self.stagecraft_client.get_module_type(module_type)
        assert get_response.status_code == 200
        if len(get_response.json()) == 0:
            post_response = self.stagecraft_client.create_module_type(
                module_type)
            module_type_id = post_response.json()['id']
        elif len(get_response.json()) > 1:
            logger.warning(
                'multiple org types for {} found, using first returned'.format(
                    module_type))
            module_type_id = get_response.json()[0]['id']
        else:
            module_type_id = get_response.json()[0]['id']
        return module_type_id


class StagecraftClient():

    def __init__(self, url, token=None):
        self.url = url
        if not token:
            self.token = 'development-oauth-access-token'
        else:
            self.token = token

    def create_dashboard(self, data):
        return self.post("/dashboard", data)

    def create_organisation(self, data):
        return self.post("/organisation/node", data)

    def create_organisation_type(self, name):
        return self.post("/organisation/type", {"name": name})

    def log_response(self, response):
        logger.debug('Response: {}: {}'.format(
            response.status_code,
            response.content
        ))

    def post(self, url, data):
        logger.debug('Posting {} to {}'.format(data, url))
        headers = {}
        headers['Authorization'] = 'Bearer {}'.format(self.token)
        headers['Content-type'] = 'application/json'
        response = requests.post(
            self.url + url, data=json.dumps(data), headers=headers)
        self.log_response(response)
        assert response.status_code == 200
        return response

    def get(self, url, params={}):
        logger.debug('Getting from {}, with params {}'.format(url, params))
        response = requests.get(
            self.url + url,
            params=params
        )
        logger.debug('Response: {}: {}'.format(
            response.status_code, response.content))
        return response

    def get_organisation(self, name, abbreviation):
        params = {}
        if abbreviation:
            params['abbreviation'] = abbreviation
            resp = self.get(
                "/organisation/node",
                params
            )
        else:
            params['name'] = name
            resp = self.get(
                "/organisation/node",
                params
            )
        return resp

    def get_organisation_type(self, name):
        return self.get(
            "/organisation/type",
            params={"name": name}
        )

    def create_module_type(self, name):
        response = self.post(
            "/module-type", {"name": name, "schema": {}}
        )
        return response

    def get_module_type(self, name):
        response = self.get(
            "/module-type", params={"name": name}
        )
        return response

    def add_module_to_dashboard(self, dashboard_id, data):
        response = self.post(
            "/dashboard/{}/module".format(dashboard_id), data
        )
        return response

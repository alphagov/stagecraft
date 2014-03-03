from __future__ import unicode_literals

import json

from nose.tools import assert_equal

from django.test import TestCase


class StatusViewsTestCase(TestCase):

    def test_status_endpoint(self):
        resp = self.client.get('/_status')
        assert_equal(resp.status_code, 200)
        expected = {'status': 'ok'}
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

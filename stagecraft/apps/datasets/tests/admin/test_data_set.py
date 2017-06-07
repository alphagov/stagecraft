from unittest import TestCase

from django.http import HttpResponseRedirect
from hamcrest import (
    assert_that, is_, instance_of, contains_string)
from httmock import urlmatch, HTTMock

from stagecraft.apps.datasets.admin.data_set import DataSetAdmin
from stagecraft.apps.datasets.tests.factories import DataSetFactory, RequestFactory


def empty_dataset_response(calls):
    @urlmatch(path=r'^/data/.*$', method='put')
    def func(url, request):
        calls.append((url.path, request))
        return {
            'status_code': 200,
            'content': '{}',
        }

    return func


class DataSetAdminTestCase(TestCase):
    def test_empty_dataset_no_confirmed(self):
        dataset = DataSetFactory()
        dataset_admin = DataSetAdmin(dataset, None)
        request = RequestFactory()
        request.method = 'POST'
        request.POST = {
            '_empty_dataset': '',
        }

        calls = []
        with HTTMock(empty_dataset_response(calls)):
            response = dataset_admin.response_change(request, dataset)

        assert_that(len(calls), is_(0))
        assert_that(response, instance_of(HttpResponseRedirect))
        assert_that(str(response.url), contains_string(str(dataset.pk)))

    def test_empty_dataset_with_confirmed(self):
        dataset = DataSetFactory()
        dataset_admin = DataSetAdmin(dataset, None)
        request = RequestFactory()
        request.method = 'POST'
        request.POST = {
            '_empty_dataset': '',
            '_confirmed': 'on',
        }

        calls = []
        with HTTMock(empty_dataset_response(calls)):
            response = dataset_admin.response_change(request, dataset)

        assert_that(len(calls), is_(1))
        assert_that(calls[0][0], is_('/data/{}/{}'.format(
            dataset.data_group.name,
            dataset.data_type.name
        )))
        assert_that(response, instance_of(HttpResponseRedirect))
        assert_that(str(response.url), contains_string(str(dataset.pk)))

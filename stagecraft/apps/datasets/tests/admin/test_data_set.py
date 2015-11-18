from django.http import HttpRequest, HttpResponseRedirect
from hamcrest import (
    assert_that, is_, instance_of, contains_string,
    equal_to)
from httmock import urlmatch, HTTMock
from unittest import TestCase
from stagecraft.apps.dashboards.tests.factories.factories import \
    DashboardFactory, ModuleFactory

from stagecraft.apps.datasets.admin.data_set import DataSetAdmin, \
    get_published_dashboards
from stagecraft.apps.datasets.tests.factories import DataSetFactory


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

    def test_empty_dataset(self):
        dataset = DataSetFactory()
        dataset_admin = DataSetAdmin(dataset, None)
        request = HttpRequest()
        request.method = 'POST'
        request.POST = {
            '_empty_dataset': '',
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

    def test_data_set_linked_to_published_dashboard(self):
        data_set = DataSetFactory()
        dashboard = DashboardFactory(status="published")
        ModuleFactory(data_set=data_set, dashboard=dashboard)

        assert_that(get_published_dashboards(data_set.name),
                    equal_to([dashboard.title]))

    def test_data_set_linked_to_unpublished_dashboard(self):
        data_set = DataSetFactory()
        dashboard = DashboardFactory(status="unpublished")
        ModuleFactory(data_set=data_set, dashboard=dashboard)

        assert_that(get_published_dashboards(data_set.name), equal_to([]))

    def test_data_set_not_linked_to_dashboard(self):
        data_set = DataSetFactory()

        assert_that(get_published_dashboards(data_set.name), equal_to([]))

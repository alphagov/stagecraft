import json

from django.test import TestCase
from hamcrest import (
    assert_that, equal_to, is_,
    has_entry, has_item, has_key, is_not, has_length
)

from stagecraft.libs.backdrop_client import disable_backdrop_connection
from ...models import Dashboard, Module, ModuleType

from stagecraft.apps.dashboards.tests.factories.factories import(
    DashboardFactory,
    ModuleFactory,
    ModuleTypeFactory)

from stagecraft.apps.datasets.tests.factories import(
    DataGroupFactory,
    DataTypeFactory,
    DataSetFactory)


class TransactionsExplorerViewsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_group = DataGroupFactory(
            name='transactional-services',
        )
        cls.data_type = DataTypeFactory(
            name='summaries',
        )
        cls.data_set = DataSetFactory(
            data_group=cls.data_group,
            data_type=cls.data_type,
        )

    @classmethod
    @disable_backdrop_connection
    def tearDownClass(cls):
        cls.data_set.delete()
        cls.data_type.delete()
        cls.data_group.delete()

    def build_dashboard(self, published=True, filter_by=[]):
        dashboard = DashboardFactory(
            published=published,
        )
        module = ModuleFactory(
            dashboard=dashboard,
            data_set=self.data_set,
            query_parameters={
                'filter_by': filter_by,
            },
        )

        return dashboard

    def test_dashboard_by_tx(self):
        dashboard = self.build_dashboard(
            published=True,
            filter_by=['service_id:hmrc-tax', 'foo:bar'],
        )
        resp = self.client.get(
            '/transactions-explorer-service/hmrc-tax/dashboard')

        assert_that(resp.status_code, is_(200))

        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), is_(1))
        assert_that(resp_json[0]['slug'], is_(dashboard.slug))

    def test_dashboard_by_tx_no_unpublished(self):
        dashboard = self.build_dashboard(
            published=False,
            filter_by=['service_id:hmrc-tax'],
        )
        resp = self.client.get(
            '/transactions-explorer-service/hmrc-tax/dashboard')

        assert_that(resp.status_code, is_(200))

        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), is_(0))

    def test_dashboard_by_tx_wrong_id(self):
        dashboard = self.build_dashboard(
            published=False,
            filter_by=['service_id:dft-driving'],
        )
        resp = self.client.get(
            '/transactions-explorer-service/hmrc-tax/dashboard')

        assert_that(resp.status_code, is_(200))

        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), is_(0))

    def test_dashboard_by_tx_id_not_first(self):
        dashboard = self.build_dashboard(
            published=True,
            filter_by=['foo:bar', 'service_id:hmrc-tax'],
        )
        resp = self.client.get(
            '/transactions-explorer-service/hmrc-tax/dashboard')

        assert_that(resp.status_code, is_(200))

        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), is_(1))
        assert_that(resp_json[0]['slug'], is_(dashboard.slug))

from django.test import TestCase
from hamcrest import assert_that, equal_to
from mock import patch
from stagecraft.apps.collectors.models import CollectorType
from stagecraft.apps.collectors.tasks import run_collector
from stagecraft.apps.collectors.tests.factories import CollectorFactory, \
    CollectorTypeFactory


class TestCeleryTasks(TestCase):

    @patch("performanceplatform.collector.ga.main")
    def test_run_collector(self, mock_ga_collector):
        # Collector Types are created through a migration and should exist in
        # the test database.
        collector_type = CollectorType.objects.get(slug="ga")
        collector = CollectorFactory(type=collector_type)

        run_collector(collector.slug, "2015-08-01", "2015-08-08")

        assert_that(mock_ga_collector.called, equal_to(True))

    @patch("performanceplatform.collector.ga.main")
    def test_run_collector_with_no_start_and_end_dates(
            self, mock_ga_collector):
        # Collector Types are created through a migration and should exist in
        # the test database.
        collector_type = CollectorType.objects.get(slug="ga")
        collector = CollectorFactory(type=collector_type)

        run_collector(collector.slug)

        assert_that(mock_ga_collector.called, equal_to(True))

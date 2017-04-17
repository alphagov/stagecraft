from django.utils import unittest
from nose.tools import assert_equal
from stagecraft.apps.collectors.models import CollectorType
from stagecraft.tools.import_collector_types import create_collector_types, \
    set_collector_type_attributes


class ImportCollectorTypesTest(unittest.TestCase):

    def test_attributes_from_schema(self):

        collector_type_schema = open(
            'stagecraft/tools/fixtures/test-collector/descriptor.json').read()

        name, slug, entry_point, provider_name = \
            set_collector_type_attributes("test-collector",
                                          collector_type_schema)

        assert_equal(name, "Test Collector")
        assert_equal(slug, "test-collector")
        assert_equal(entry_point,
                     "performanceplatform.collector.test.collector")
        assert_equal(provider_name, "test")

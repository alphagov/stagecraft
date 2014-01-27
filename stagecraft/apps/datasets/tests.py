# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from django.test import TestCase

from nose.tools import assert_equal


class DummyTestCase(TestCase):
    def test_nothing_at_all(self):
        assert_equal(True, True)

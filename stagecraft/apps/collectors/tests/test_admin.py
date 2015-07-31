from django.test import TestCase
from hamcrest import assert_that, contains_string, not_none

from stagecraft.apps.collectors.tests.factories import CollectorFactory
from stagecraft.apps.collectors.models import DataSource

from stagecraft.apps.collectors import admin


class SelecWithDataTestCase(TestCase):

    def setUp(self):
        self.option_value = (
            ('be51c49a-3fe8-4c8b-b7f7-636e34da15c4'),
            ('beb0e8d4-ebdb-4768-bc41-767f73b32fba'))
        self.option_label = (u'Google Analytics: MOJ')
        self.select_with_data = admin.SelectWithData()

    def test_render_option_with_data_id(self):
        selected_choices = (set([u'43b099a6-dd76-4631-8cae-afe86923d331']))
        render_option = self.select_with_data.render_option(
            selected_choices, self.option_value, self.option_label)

        assert_that(render_option, contains_string(
            'data-id="beb0e8d4-ebdb-4768-bc41-767f73b32fba"'))

    def test_id_removed_from_single_select(self):
        selected_choices = (set(
            [u'43b099a6-dd76-4631-8cae-afe86923d331',
             u'be51c49a-3fe8-4c8b-b7f7-636e34da15c4']))
        render_option = self.select_with_data.render_option(
            selected_choices, self.option_value, self.option_label)

        assert_that(render_option, contains_string(
            'be51c49a-3fe8-4c8b-b7f7-636e34da15c4'))
        assert_that(
            render_option, not(contains_string(
                '43b099a6-dd76-4631-8cae-afe86923d331')))


class CollectorModelChoiceIteratorTestCase(TestCase):

    def test_each_choices_tuple_contains_three_values(self):

        collector1 = CollectorFactory()
        queryset = DataSource.objects.all()
        choice_instance = admin.CollectorModelChoiceField(queryset)
        choices = choice_instance._get_choices()
        iteration = list(choices.__iter__())
        iter_choice = iteration[1]
        first_value = iter_choice[0][1]
        second_value = iter_choice[0][0]
        third_value = iter_choice[1]

        assert_that(first_value, not_none)
        assert_that(second_value, not_none)
        assert_that(third_value, contains_string('provider-1: data-source-1'))


from django.db import transaction, IntegrityError
from django.test import TestCase, TransactionTestCase
from jsonschema.exceptions import ValidationError
from hamcrest import (
    assert_that, equal_to, calling, raises, is_not
)

from ...models.dashboard import Dashboard
from ...models.module import Module, ModuleType


class ModuleTestCase(TestCase):

    def test_cannot_have_two_equal_slugs_on_one_dashboard(self):
        dashboard_a = Dashboard.objects.create(
            slug='a-dashboard',
            published=False,
        )
        dashboard_b = Dashboard.objects.create(
            slug='b-dashboard',
            published=False,
        )
        module_type = ModuleType.objects.create(
            name='graph'
        )

        def create_module(dashboard_model):
            with transaction.atomic():
                Module.objects.create(
                    slug='a-module',
                    type=module_type,
                    dashboard=dashboard_model
                )

        create_module(dashboard_a)
        assert_that(
            calling(create_module).with_args(dashboard_a),
            raises(IntegrityError))
        assert_that(
            calling(create_module).with_args(dashboard_b),
            is_not(raises(IntegrityError)))

    def test_options_validated_against_type(self):
        dashboard = Dashboard.objects.create(
            slug='a-dashboard',
            published=False,
        )
        module_type = ModuleType.objects.create(
            name='graph',
            schema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "maxLength": 3
                    }
                }
            }
        )

        module = Module(
            slug='a-module',
            type=module_type,
            dashboard=dashboard,
            options={
                'title': 'bar'
            }
        )

        assert_that(
            calling(lambda: module.validate_options()),
            is_not(raises(ValidationError))
        )

        module.options = {
            'title': 'foobar'
        }

        assert_that(
            calling(lambda: module.validate_options()),
            raises(ValidationError)
        )

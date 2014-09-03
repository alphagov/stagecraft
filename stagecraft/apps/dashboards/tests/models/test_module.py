
from django.db import transaction, IntegrityError
from django.test import TestCase, TransactionTestCase
from jsonschema.exceptions import ValidationError, SchemaError
from hamcrest import (
    assert_that, equal_to, calling, raises, is_not, has_entry, has_key
)

from ...models.dashboard import Dashboard
from ...models.module import Module, ModuleType


class ModuelTypeTestCase(TestCase):

    def test_module_type_serialization(self):
        module_type = ModuleType.objects.create(
            name='foo',
            schema={
                'some': 'thing',
            }
        )

        assert_that(module_type.serialize(), has_key('id'))
        assert_that(module_type.serialize(), has_entry('name', 'foo'))
        assert_that(
            module_type.serialize(),
            has_entry('schema', {'some': 'thing'}))

    def test_schema_validation(self):
        module_type = ModuleType(
            name='foo',
            schema={"type": "some made up type"}
        )
        assert_that(
            calling(module_type.validate_schema),
            raises(SchemaError)
        )

        module_type.schema = {"type": "string"}
        assert_that(
            calling(module_type.validate_schema),
            is_not(raises(SchemaError))
        )


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

    def test_query_params_validated(self):
        dashboard = Dashboard.objects.create(
            slug='a-dashboard',
            published=False,
        )
        module_type = ModuleType.objects.create(
            name='graph',
        )

        module = Module(
            slug='a-module',
            type=module_type,
            dashboard=dashboard,
            query_parameters={
                "collect": ["foo:not-a-thing"],
            }
        )

        assert_that(
            calling(lambda: module.validate_query_parameters()),
            raises(ValidationError)
        )

        module.query_parameters["collect"][0] = "foo:sum"

        assert_that(
            calling(lambda: module.validate_query_parameters()),
            is_not(raises(ValidationError))
        )

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

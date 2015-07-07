import unittest

from hamcrest import (
    assert_that, is_, contains_string
)

from nose.tools import assert_equal

from .factories import TransformTypeFactory, TransformFactory

from stagecraft.apps.datasets.tests.factories import DataTypeFactory

from ..models import Transform, TransformType

from stagecraft.apps.users.models import User


class TransformTest(unittest.TestCase):

    def test_schema_validation(self):
        transform_type = TransformTypeFactory(
            schema={
                "type": "object",
                "properties": {
                    "foo": {"type": "string"},
                },
            }
        )

        transform = Transform()
        transform.type = transform_type
        transform.query_parameters = {}
        transform.options = {
            "foo": 1,
        }

        assert_that(
            transform.validate(),
            contains_string('options are invalid')
        )

        transform.options = {
            "foo": "bar",
        }

        assert_that(transform.validate(), is_(None))

    def test_query_validation(self):
        transform_type = TransformTypeFactory()
        transform = Transform()
        transform.type = transform_type
        transform.query_parameters = {
            'start_at': 1,  # it should be a string
        }

        assert_that(
            transform.validate(),
            contains_string('query parameters are invalid')
        )

        transform.query_parameters['start_at'] = '2014-09-11'

        assert_that(transform.validate(), is_(None))

    def test_can_create_transform_with_owner(self):
        transform = Transform()
        data_type_input = DataTypeFactory()
        data_type_output = DataTypeFactory()
        transform_type = TransformTypeFactory()

        transform1 = Transform(
            input_type=data_type_input,
            output_type=data_type_output,
            type=transform_type
            )
        user, _ = User.objects.get_or_create(
            email='foobar.lastname@gov.uk')
        transform1.save()
        transform1.owners.add(user)

        assert_equal('foobar.lastname@gov.uk', transform1.owners.first().email)

    def test_can_create_transform_without_owner(self):
        transform = Transform()
        data_type_input = DataTypeFactory()
        data_type_output = DataTypeFactory()
        transform_type = TransformTypeFactory()

        transform1 = Transform(
            input_type=data_type_input,
            output_type=data_type_output,
            type=transform_type
            )
        transform1.save()

        assert_equal(len(transform1.owners.all()), 0)

    def test_can_create_transform_without_owner_in_forms(self):

        assert_equal(Transform._meta.get_field('owners').blank, True)


class TransformTypeTest(unittest.TestCase):

    def test_schema_validation(self):
        transform_type = TransformType()

        transform_type.schema = {
            "$schema": False,
        }

        err = transform_type.validate()
        assert_that(err, contains_string('schema is invalid'))

        transform_type.schema = {
            "$schema": "a schema",
        }

        err = transform_type.validate()
        assert_that(err, is_(None))

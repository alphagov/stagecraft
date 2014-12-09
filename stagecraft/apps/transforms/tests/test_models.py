import unittest

from hamcrest import (
    assert_that, is_, contains_string
)

from .factories import TransformTypeFactory, TransformFactory

from ..models import Transform, TransformType


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

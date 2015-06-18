import json

from django.test import TestCase
from hamcrest import (
    assert_that, equal_to, has_key
)

from .factories import (TransformTypeFactory, TransformFactory,
                        TransformWithDataGroupFactory)
from ...datasets.tests.factories import DataGroupFactory, DataTypeFactory
from stagecraft.apps.users.models import User
from stagecraft.apps.transforms.models import Transform
from stagecraft.libs.authorization.tests.test_http import with_govuk_signon


class TransformTypeViewTestCase(TestCase):

    def test_post(self):
        payload = {
            "name": "some-type",
            "function": "backdrop.some.function",
            "schema": {},
        }

        resp = self.client.post(
            '/transform-type',
            data=json.dumps(payload),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json['name'], equal_to('some-type'))
        assert_that(resp_json['function'], equal_to('backdrop.some.function'))
        assert_that(resp_json['schema'], equal_to({}))

    def test_get(self):
        transform_type = TransformTypeFactory()
        resp = self.client.get(
            '/transform-type/{}'.format(transform_type.id),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json['id'], equal_to(str(transform_type.id)))
        assert_that(resp_json['name'], equal_to(transform_type.name))
        assert_that(resp_json['function'], equal_to(transform_type.function))
        assert_that(resp_json['schema'], equal_to(transform_type.schema))


class TransformViewTestCase(TestCase):

    def test_post(self):
        transform_type = TransformTypeFactory()
        input_data_type = DataTypeFactory()
        input_data_group = DataGroupFactory()
        output_data_type = DataTypeFactory()
        output_data_group = DataGroupFactory()

        payload = {
            "type_id": str(transform_type.id),
            "input": {
                "data-type": input_data_type.name,
                "data-group": input_data_group.name,
            },
            "query-parameters": {},
            "options": {},
            "output": {
                "data-type": output_data_type.name,
                "data-group": output_data_group.name,
            },
        }

        resp = self.client.post(
            '/transform',
            data=json.dumps(payload),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json['type']['id'], equal_to(str(transform_type.id)))
        assert_that(
            resp_json['input']['data-type'],
            equal_to(input_data_type.name))
        assert_that(
            resp_json['input']['data-group'],
            equal_to(input_data_group.name))
        assert_that(
            resp_json['output']['data-type'],
            equal_to(output_data_type.name))
        assert_that(
            resp_json['output']['data-group'],
            equal_to(output_data_group.name))

        assert_that(
            Transform.objects.get(id=resp_json['id']).owners.first().email,
            equal_to('some.user@digital.cabinet-office.gov.uk')
        )

    def test_post_type_not_found(self):
        resp = self.client.post(
            '/transform',
            data=json.dumps({
                "type_id": "00000000-0000-0000-0000-000000000000",
                "input": {
                    "data-type": DataTypeFactory().name,
                },
                "options": {},
                "output": {
                    "data-type": DataTypeFactory().name,
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_post_requires_input_type(self):
        resp = self.client.post(
            '/transform',
            data=json.dumps({
                "type_id": str(TransformTypeFactory().id),
                "input": {
                    "data-type": "not-a-data-type",
                },
                "options": {},
                "output": {
                    "data-type": DataTypeFactory().name,
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_post_requires_output_type(self):
        resp = self.client.post(
            '/transform',
            data=json.dumps({
                "type_id": str(TransformTypeFactory().id),
                "input": {
                    "data-type": DataTypeFactory().name,
                },
                "options": {},
                "output": {
                    "data-type": "not-a-data-type",
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_get_gets_transform(self):
        transform = TransformFactory()
        resp = self.client.get(
            '/transform/{}'.format(transform.id),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json['id'], equal_to(str(transform.id)))
        assert_that(
            resp_json['input']['data-type'],
            equal_to(transform.input_type.name)
        )

    @with_govuk_signon(permissions=['transforms'])
    def test_get_returns_404_when_user_not_in_ownership_array(self):
        transform = TransformFactory()
        assert_that(len(transform.owners.all()), equal_to(0))
        resp = self.client.get(
            '/transform/{}'.format(transform.id),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(404))

    @with_govuk_signon(permissions=['transforms'])
    def test_list_returns_empty_list_when_user_not_in_ownership_array(self):
        transform = TransformFactory()
        assert_that(len(transform.owners.all()), equal_to(0))
        resp = self.client.get(
            '/transform/',
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json')

        assert_that(json.loads(resp.content), equal_to([]))

    @with_govuk_signon(permissions=['transforms'])
    def test_list_returns_transform_in_list_when_user_in_ownership_array(self):
        transform = TransformWithDataGroupFactory()
        user, _ = User.objects.get_or_create(
            email='foobar.lastname@gov.uk')
        transform.owners.add(user)
        resp = self.client.get(
            '/transform/',
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json')

        resp_json = json.loads(resp.content)
        assert_that(len(resp_json), equal_to(1))
        assert_that(
            resp_json[0]['type']['id'],
            equal_to(str(transform.type.id)))
        assert_that(
            resp_json[0]['input']['data-type'],
            equal_to(transform.input_type.name))
        assert_that(
            resp_json[0]['input']['data-group'],
            equal_to(transform.input_group.name))
        assert_that(
            resp_json[0]['output']['data-type'],
            equal_to(transform.output_type.name))
        assert_that(
            resp_json[0]['output']['data-group'],
            equal_to(transform.output_group.name))

    @with_govuk_signon(permissions=['transforms'])
    def test_404_on_put_when_user_not_in_ownership_array(self):
        transform = TransformFactory()
        user, _ = User.objects.get_or_create(
            email='not_correct_user.lastname@gov.uk')
        transform.owners.add(user)

        resp = self.client.put(
            '/transform/{}'.format(transform.id),
            data={},
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )

        assert_that(resp.status_code, equal_to(404))

    @with_govuk_signon(permissions=['transforms'])
    def test_successful_put_when_user_in_ownership_array(self):
        transform = TransformFactory()
        user, _ = User.objects.get_or_create(
            email='foobar.lastname@gov.uk')
        transform.owners.add(user)

        resp = self.client.put(
            '/transform/{}'.format(transform.id),
            data=json.dumps({
                "type_id": str(TransformTypeFactory().id),
                "input": {
                    "data-type": DataTypeFactory().name,
                },
                "query-parameters": {},
                "options": {},
                "output": {
                    "data-type": DataTypeFactory().name
                }
            }),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )

        assert_that(resp.status_code, equal_to(200))

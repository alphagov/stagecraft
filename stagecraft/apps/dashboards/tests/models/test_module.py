
from django.db import transaction, IntegrityError
from django.test import TestCase
from jsonschema.exceptions import ValidationError
from stagecraft.apps.users.models import User
from hamcrest import (
    assert_that, equal_to, calling, raises, is_not, has_entry, has_key,
    contains,
    contains_string, is_)

from stagecraft.libs.backdrop_client import disable_backdrop_connection

from ...models.module import Module, ModuleType

from stagecraft.apps.dashboards.tests.factories.factories import(
    DashboardFactory,
    ModuleFactory,
    ModuleTypeFactory)

from stagecraft.apps.datasets.tests.factories import(
    DataGroupFactory,
    DataTypeFactory,
    DataSetFactory)


class ModuleTypeTestCase(TestCase):

    def test_module_type_serialization(self):
        module_type = ModuleTypeFactory(
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
            schema={'properties': 'true'}
        )
        err = module_type.validate()
        assert_that(err, contains_string('schema is invalid'))

        module_type.schema = {"type": "string"}
        err = module_type.validate()
        assert_that(err, is_(None))


class ModuleTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_group = DataGroupFactory(name='group')
        cls.data_type = DataTypeFactory(name='type')
        cls.data_set = DataSetFactory(
            data_group=cls.data_group,
            data_type=cls.data_type,
        )
        cls.module_type = ModuleTypeFactory(name='graph', schema={})
        cls.dashboard_a = DashboardFactory(
            slug='a-dashboard',
            published=False)
        cls.dashboard_b = DashboardFactory(
            slug='b-dashboard',
            published=False)

    @classmethod
    @disable_backdrop_connection
    def tearDownClass(cls):
        cls.data_set.delete()
        cls.data_type.delete()
        cls.data_group.delete()
        cls.module_type.delete()
        cls.dashboard_a.delete()
        cls.dashboard_b.delete()

    def test_spotlightify(self):
        module = ModuleFactory(
            slug='a-module',
            type=self.module_type,
            dashboard=self.dashboard_a,
            data_set=self.data_set,
            order=1,
            options={
                'foo': 'bar',
            },
            query_parameters={
                'sort_by': 'foo'
            })

        spotlight_module = module.spotlightify()

        assert_that(spotlight_module['slug'], equal_to('a-module'))
        assert_that(spotlight_module['foo'], equal_to('bar'))
        assert_that(
            spotlight_module['module-type'],
            equal_to(self.module_type.name))
        assert_that(
            spotlight_module['data-source']['data-group'],
            equal_to(self.data_group.name))
        assert_that(
            spotlight_module['data-source']['data-type'],
            equal_to(self.data_type.name))
        assert_that(
            spotlight_module['data-source']['query-params']['sort_by'],
            equal_to('foo'))

    def test_spotlightify_with_nested_modules(self):
        parent = ModuleFactory(slug='a-module', order=1)
        child = ModuleFactory(slug='b-module', order=2, parent=parent)
        ModuleFactory(
            slug='c-module', order=3, parent=child)
        other_child = ModuleFactory(slug='d-module', order=4, parent=parent)

        spotlightify = parent.spotlightify()

        assert_that(
            spotlightify,
            has_entry('modules',
                      contains(child.spotlightify(),
                               other_child.spotlightify()))
        )

    def test_spotlightify_with_no_data_set(self):
        module = ModuleFactory(
            slug='a-module',
            type=self.module_type,
            dashboard=self.dashboard_a,
            order=1,
            options={
                'foo': 'bar',
            },
            query_parameters={
                'sort_by': 'foo'
            })

        spotlight_module = module.spotlightify()

        assert_that(spotlight_module['slug'], equal_to('a-module'))
        assert_that(spotlight_module['foo'], equal_to('bar'))
        assert_that(
            spotlight_module['module-type'],
            equal_to(self.module_type.name))
        assert_that(
            spotlight_module,
            is_not(has_key('data-source')))

    def test_serialize_with_no_dataset(self):
        module = ModuleFactory(
            slug='a-module',
            type=self.module_type,
            order=1,
            dashboard=self.dashboard_a)

        serialization = module.serialize()

        assert_that(serialization['slug'], equal_to('a-module'))
        assert_that(
            serialization['type']['id'],
            equal_to(str(self.module_type.id)))
        assert_that(
            serialization['dashboard']['id'],
            equal_to(str(self.dashboard_a.id)))

        assert_that(serialization['query_parameters'], equal_to(None))
        assert_that(serialization['data_set'], equal_to(None))

    def test_serialize_with_dataset(self):
        module = ModuleFactory(
            slug='a-module',
            type=self.module_type,
            order=1,
            data_set=self.data_set,
            dashboard=self.dashboard_a,
            query_parameters={"foo": "bar"})

        serialization = module.serialize()

        assert_that(serialization['slug'], equal_to('a-module'))
        assert_that(
            serialization['type']['id'],
            equal_to(str(self.module_type.id)))
        assert_that(
            serialization['dashboard']['id'],
            equal_to(str(self.dashboard_a.id)))

        assert_that(
            serialization['query_parameters'],
            has_entry('foo', 'bar'))
        assert_that(
            serialization, has_entry(
                'data_group',
                equal_to(self.data_set.data_group.name)))
        assert_that(
            serialization, has_entry(
                'data_type',
                equal_to(self.data_set.data_type.name)))

    def test_serialize_with_dataset_but_no_query_parameters(self):
        module = ModuleFactory(
            slug='a-module',
            type=self.module_type,
            data_set=self.data_set,
            order=1,
            dashboard=self.dashboard_a)

        serialization = module.serialize()

        assert_that(serialization['slug'], equal_to('a-module'))
        assert_that(
            serialization['type']['id'],
            equal_to(str(self.module_type.id)))
        assert_that(
            serialization['dashboard']['id'],
            equal_to(str(self.dashboard_a.id)))

        assert_that(serialization['query_parameters'], equal_to(None))
        assert_that(
            serialization,
            has_entry(
                'data_group', equal_to(self.data_set.data_group.name)))

        assert_that(
            serialization,
            has_entry(
                'data_type', equal_to(self.data_set.data_type.name)))

    def test_serialize_with_no_nested_modules(self):
        module = ModuleFactory(
            slug='a-module',
            type=self.module_type,
            options={},
            query_parameters={},
            order=1,
            dashboard=self.dashboard_a)

        serialization = module.serialize()

        assert_that(serialization['modules'], equal_to([]))
        assert_that(serialization['parent'], equal_to(None))

    def test_serialize_with_nested_modules(self):
        parent = ModuleFactory(slug='a-module', order=1)
        child = ModuleFactory(slug='b-module', order=2, parent=parent)
        ModuleFactory(
            slug='c-module', order=3, parent=child)
        other_child = ModuleFactory(slug='d-module', order=4, parent=parent)

        serialization = parent.serialize()

        assert_that(
            serialization,
            has_entry('modules',
                      contains(child.serialize(), other_child.serialize())))
        assert_that(
            serialization['modules'][0]['parent'],
            has_entry('id', str(parent.id)))

    def test_cannot_have_two_equal_slugs_on_one_dashboard(self):
        def create_module(dashboard_model):
            with transaction.atomic():
                ModuleFactory(
                    slug='a-module',
                    type=self.module_type,
                    dashboard=dashboard_model,
                    order=1,
                )

        create_module(self.dashboard_a)
        assert_that(
            calling(create_module).with_args(self.dashboard_a),
            raises(IntegrityError))
        assert_that(
            calling(create_module).with_args(self.dashboard_b),
            is_not(raises(IntegrityError)))

    def test_query_params_validated(self):
        module = Module(
            slug='a-module',
            type=self.module_type,
            dashboard=self.dashboard_a,
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
        module_type = ModuleTypeFactory(
            name='some-graph',
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
            dashboard=self.dashboard_a,
            options={
                'title': 'bar'
            }
        )

        assert_that(
            calling(lambda: module.validate_options()),
            is_not(raises(ValidationError))
        )

        module.options = {'title': 'foobar'}

        assert_that(
            calling(lambda: module.validate_options()),
            raises(ValidationError)
        )

    def test_group_by_is_rewritten_to_be_a_list(self):
        module = Module.objects.create(
            title='a-title',
            slug='a-module',
            type=self.module_type,
            dashboard=self.dashboard_a,
            data_set=self.data_set,
            order=1,
            query_parameters={
                'group_by': 'foo'
            })

        module.full_clean()

        assert_that(module.query_parameters['group_by'],
                    equal_to(['foo']))

    def test_list_group_by_is_unchanged(self):
        module = Module.objects.create(
            title='a-title',
            slug='a-module',
            type=self.module_type,
            dashboard=self.dashboard_a,
            data_set=self.data_set,
            order=1,
            query_parameters={
                'group_by': ['foo']
            })

        module.full_clean()

        assert_that(module.query_parameters['group_by'],
                    equal_to(['foo']))

    def test_no_group_by_is_unchanged(self):
        module = Module.objects.create(
            title='a-title',
            slug='a-module',
            type=self.module_type,
            dashboard=self.dashboard_a,
            data_set=self.data_set,
            order=1,
            query_parameters={}
        )

        module.full_clean()

        assert_that(module.query_parameters.get('group_by'),
                    equal_to(None))

    def test_tabs_group_by_is_rewritten_to_be_a_list(self):
        module = Module.objects.create(
            title='a-title',
            slug='a-module',
            type=self.module_type,
            dashboard=self.dashboard_a,
            data_set=self.data_set,
            order=1,
            options={
                'tabs': [
                    {
                        'data-source': {
                            'query-params': {
                                'group_by': 'foo'
                            }
                        }
                    },
                    {}
                ]
            })

        module.full_clean()

        data_source = module.options['tabs'][0]['data-source']
        assert_that(data_source['query-params']['group_by'],
                    equal_to(['foo']))

    def test_module_delegates_to_dashboard_owners(self):
        module = ModuleFactory(
            slug='a-module',
            type=self.module_type,
            dashboard=self.dashboard_a,
            order=1,
            options={
                'foo': 'bar',
            },
            query_parameters={
                'sort_by': 'foo'
            })
        user, _ = User.objects.get_or_create(
            email='foobar.lastname@gov.uk')
        self.dashboard_a.owners.add(user)
        assert_that(
            module.owners.all(),
            self.dashboard_a.owners.all())


from django.db import transaction, IntegrityError
from django.test import TestCase, TransactionTestCase
from jsonschema.exceptions import ValidationError, SchemaError
from hamcrest import (
    assert_that, equal_to, calling, raises, is_not, has_entry, has_key
)

from stagecraft.apps.datasets.models import DataGroup, DataType, DataSet
from stagecraft.libs.backdrop_client import disable_backdrop_connection

from ...models.dashboard import Dashboard
from ...models.module import Module, ModuleType


class ModuleTypeTestCase(TestCase):

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

    @classmethod
    def setUpClass(cls):
        cls.data_group = DataGroup.objects.create(name='group')
        cls.data_type = DataType.objects.create(name='type')
        cls.data_set = DataSet.objects.create(
            data_group=cls.data_group,
            data_type=cls.data_type,
        )
        cls.module_type = ModuleType.objects.create(name='graph')
        cls.dashboard_a = Dashboard.objects.create(
            slug='a-dashboard',
            published=False)
        cls.dashboard_b = Dashboard.objects.create(
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

    def test_serialize_with_no_dataset(self):
        module = Module.objects.create(
            slug='a-module',
            type=self.module_type,
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

        module.delete()

    def test_serialize_with_dataset(self):
        module = Module.objects.create(
            slug='a-module',
            type=self.module_type,
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
            serialization['data_set']['id'],
            equal_to(self.data_set.id))

        module.delete()

    def test_serialize_with_dataset_but_no_query_parameters(self):
        module = Module.objects.create(
            slug='a-module',
            type=self.module_type,
            data_set=self.data_set,
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
            serialization['data_set']['id'],
            equal_to(self.data_set.id))

        module.delete()

    def test_cannot_have_two_equal_slugs_on_one_dashboard(self):
        def create_module(dashboard_model):
            with transaction.atomic():
                Module.objects.create(
                    slug='a-module',
                    type=self.module_type,
                    dashboard=dashboard_model
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
        module_type = ModuleType.objects.create(
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

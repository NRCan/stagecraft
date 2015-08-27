from django.test import TestCase
from stagecraft.apps.collectors.management.lib.collectors_to_data_source_attribute_list import get_data_source_attribute_list  # noqa
from hamcrest import equal_to, assert_that, has_item, has_entry
from stagecraft.apps.collectors.tests.factories import CollectorFactory
from stagecraft.apps.dashboards.tests.factories.factories import(ModuleFactory)
from stagecraft.apps.dashboards.tests.factories.factories import(
    DepartmentFactory)


class CollectorsToDataSourceTestCase(TestCase):

    def test_get_list_returns_a_list_of_data_source_attrs(self):
        collector = CollectorFactory()
        module = ModuleFactory(data_set=collector.data_set)
        department = DepartmentFactory()
        dashboard = module.dashboard
        dashboard.organisation = department
        dashboard.save()
        data_source_attr_list = get_data_source_attribute_list()
        assert_that(
            data_source_attr_list,
            has_item(has_entry("name", "abc")))
        assert_that(len(data_source_attr_list), equal_to(1))

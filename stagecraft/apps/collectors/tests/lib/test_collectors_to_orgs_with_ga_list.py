from django.test import TestCase
from stagecraft.apps.collectors.lib.collectors_to_orgs_with_ga_list import get_list_of_orgs_with_ga  # noqa
from hamcrest import equal_to, assert_that, has_item
from stagecraft.apps.collectors.tests.factories import CollectorFactory
from stagecraft.apps.dashboards.tests.factories.factories import(ModuleFactory)
from stagecraft.apps.dashboards.tests.factories.factories import(
    DepartmentFactory)
from stagecraft.apps.collectors.models import Provider


class CollectorsToOrgsWithGaListTestCase(TestCase):

    def test_get_list_returns_a_list_of_data_source_attrs(self):
        Provider.objects.all().delete()
        collector = CollectorFactory()
        provider = collector.type.provider
        provider.slug = "ga"
        provider.save()
        module = ModuleFactory(data_set=collector.data_set)
        department = DepartmentFactory()
        dashboard = module.dashboard
        dashboard.organisation = department
        dashboard.save()
        orgs_with_ga = get_list_of_orgs_with_ga()
        assert_that(
            orgs_with_ga,
            has_item("For {} {} provides {}".format(
                department.name,
                collector.type.provider.name,
                collector.data_set.name)))
        assert_that(len(orgs_with_ga), equal_to(1))

    def test_get_list_returns_an_empty_list_if_no_ga(self):
        collector = CollectorFactory()
        module = ModuleFactory(data_set=collector.data_set)
        department = DepartmentFactory()
        dashboard = module.dashboard
        dashboard.organisation = department
        dashboard.save()
        orgs_with_ga = get_list_of_orgs_with_ga()
        assert_that(len(orgs_with_ga), equal_to(0))

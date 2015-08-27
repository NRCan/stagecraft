from stagecraft.apps.collectors.models import Collector
from stagecraft.apps.dashboards.models.module import(
    Module)
from stagecraft.apps.dashboards.models.dashboard import(
    Dashboard)


def get_list_of_orgs_with_ga():
    data_source_attribute_list = []
    for collector in Collector.objects.all():
        if collector.type.provider.slug == "ga":
            org_names_list = get_org_list_through_dashboard(collector)
            org_names_list = list(set(org_names_list))
            if len(org_names_list) > 1:
                print "loads! {}".format(org_names_list)
                raise "blow up"
            if org_names_list:
                data_source_attribute_list.append(
                    "For {} {} provides {}".format(
                        org_names_list[0],
                        collector.type.provider.name,
                        collector.data_set.name))
    print data_source_attribute_list
    return data_source_attribute_list


def get_org_list_through_dashboard(collector):
    modules = Module.objects.filter(data_set=collector.data_set).all()
    dashboard_ids = [module.dashboard_id for module in modules]
    dashboards = Dashboard.objects.filter(id__in=dashboard_ids)
    return [dashboard.organisation.name for dashboard in dashboards]

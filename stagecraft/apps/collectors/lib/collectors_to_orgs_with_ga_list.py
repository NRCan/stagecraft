from stagecraft.apps.collectors.models import Collector
from stagecraft.apps.dashboards.models.module import(
    Module)
from stagecraft.apps.dashboards.models.dashboard import(
    Dashboard)


def get_data_source_attribute_list():
    data_source_attribute_list = []
    for collector in Collector.objects.all():
        org_names_list = get_org_list_through_dashboard(collector)
        org_names_set = list(set(org_names_list))
        if len(org_names_set) > 1:
            print "loads! {}".format(org_names_set)
        data_source_attribute_list.append({
            'name': "{} {}".format(
                org_names_set[0], collector.type.provider.name)
        })
    return data_source_attribute_list


def get_org_list_through_dashboard(collector):
    modules = Module.objects.filter(data_set=collector.data_set).all()
    dashboard_ids = [module.dashboard_id for module in modules]
    dashboards = Dashboard.objects.filter(id__in=dashboard_ids)
    return [dashboard.organisation.name for dashboard in dashboards]

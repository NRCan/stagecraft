from stagecraft.apps.collectors.models import Collector
from stagecraft.apps.dashboards.models.module import(
    Module)
from stagecraft.apps.dashboards.models.dashboard import(
    Dashboard)


def get_list_of_orgs_with_ga():
    data_source_attribute_list = []
    all_org_names = set()
    for collector in Collector.objects.all():
        if collector.type.provider.slug == "ga":

            for owner in collector.data_set.owners.all():
                if "digital.cabinet-office.gov.uk" not in owner.email:
                    print owner.email
            org_names_list = get_org_list_through_dashboard(collector)
            org_names_set = set(org_names_list)
            org_names_list = list(org_names_set)
            all_org_names = all_org_names.union(org_names_set)
            if org_names_list:
                for org in org_names_list:
                    data_source_attribute_list.append(
                        "For {} {} provides {}".format(
                            org,
                            collector.type.provider.name,
                            collector.data_set.name))
    print data_source_attribute_list
    print all_org_names
    return data_source_attribute_list


def get_org_list_through_dashboard(collector):
    modules = Module.objects.filter(data_set=collector.data_set).all()
    dashboard_ids = [module.dashboard_id for module in modules]
    dashboards = Dashboard.objects.filter(id__in=dashboard_ids)
    for dashboard in dashboards:
        for owner in dashboard.owners.all():
            if "digital.cabinet-office.gov.uk" not in owner.email:
                print owner.email
        for module in dashboard.module_set.all():
            if module.data_set:
                for owner in module.data_set.owners.all():
                    if "digital.cabinet-office.gov.uk" not in owner.email:
                        print owner.email
    return [dashboard.organisation.name for dashboard in dashboards if dashboard.organisation is not None]

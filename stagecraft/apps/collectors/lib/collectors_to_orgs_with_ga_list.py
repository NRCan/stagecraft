from stagecraft.apps.collectors.models import Collector
from stagecraft.apps.dashboards.models.module import(
    Module)
from stagecraft.apps.dashboards.models.dashboard import(
    Dashboard)
import json

for_collector = {}

dashboards_to_emails = {}


def get_list_of_orgs_with_ga():
    data_source_attribute_list = []
    all_org_names = set()
    for collector in Collector.objects.all():
        if collector.type.provider.slug == "ga":
            for_collector_data_set = {collector.data_set.name: []}
            for owner in collector.data_set.owners.all():
                if "digital.cabinet-office.gov.uk" not in owner.email:
                    for_collector_data_set[collector.data_set.name].append(
                        owner.email)
                    # print owner.email
            org_names_list, for_collector_dashboards = \
                get_org_list_through_dashboard(collector)
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
            if for_collector_data_set[collector.data_set.name]:
                for_collector[collector.slug] = {
                    'data_set': for_collector_data_set,
                    'dashboards': for_collector_dashboards}
            else:
                for_collector[collector.slug] = {
                    'dashboards': for_collector_dashboards}
    # print data_source_attribute_list
    # print all_org_names

    with open('emailz.json', 'w') as f:
        f.write(json.dumps(for_collector, indent=4, sort_keys=True))

    with open('dashboards_to_emails.csv', 'w') as f:
        f.write('Dashboard,Email\n')
    with open('dashboards_to_emails.csv', 'a') as f:
        for dashboard, emails in dashboards_to_emails.iteritems():
            f.write('{},{}\n'.format(dashboard, ', '.join(list(emails))))
    print json.dumps(for_collector, indent=4, sort_keys=True)
    return data_source_attribute_list


def get_org_list_through_dashboard(collector):
    for_collector_dashboards = {}
    modules = Module.objects.filter(data_set=collector.data_set).all()
    dashboard_ids = [module.dashboard_id for module in modules]
    dashboards = Dashboard.objects.filter(id__in=dashboard_ids)
    for dashboard in dashboards:
        for_collector_dashboards[dashboard.slug] = {}
        for owner in dashboard.owners.all():
            if "digital.cabinet-office.gov.uk" not in owner.email:
                if 'owners' in for_collector_dashboards[dashboard.slug]:
                    for_collector_dashboards['owners'].append(owner.email)
                else:
                    for_collector_dashboards['owners'] = [owner.email]
                if dashboard.slug in dashboards_to_emails is not None:
                    dashboards_to_emails[dashboard.slug].update([owner.email])
                else:
                    dashboards_to_emails[dashboard.slug] = set([owner.email])
                # print owner.email
        modules_to_owners = {}
        for module in dashboard.module_set.all():
            if module.data_set:
                for owner in module.data_set.owners.all():
                    if "digital.cabinet-office.gov.uk" not in owner.email:
                        if module.slug in modules_to_owners:
                            modules_to_owners[module.slug].append(owner.email)
                        else:
                            modules_to_owners[module.slug] = [owner.email]
                        if dashboard.slug in dashboards_to_emails is not None:
                            dashboards_to_emails[dashboard.slug].update(
                                [owner.email])
                        else:
                            dashboards_to_emails[dashboard.slug] = set(
                                [owner.email])
                        # print owner.email
        for_collector_dashboards[dashboard.slug]['modules'] = \
            modules_to_owners
    return [dashboard.organisation.name for dashboard in dashboards
            if dashboard.organisation is not None], for_collector_dashboards

import django
import cPickle as pickle
import os
import requests
import sys
from stagecraft.apps.organisation.models import Node, NodeType
from stagecraft.apps.dashboards.models import Dashboard

from collections import defaultdict
# from spreadsheets import SpreadsheetMunger


def get_govuk_organisations():
    def get_page(page):
        response = requests.get(
            'https://www.gov.uk/api/organisations?page={}'.format(page))
        return response.json()

    first_page = get_page(1)
    results = first_page['results']

    for page_num in range(2, first_page['pages'] + 1):
        page = get_page(page_num)
        results = results + page['results']

    return results


def load_data(username, password):
    # spreadsheets = SpreadsheetMunger({
        # 'names_name': 8,
        # 'names_slug': 9,
        # 'names_service_name': 6,
        # 'names_service_slug': 7,
        # 'names_tx_id_column': 18,
    # })
    # transactions_data = spreadsheets.load(username, password)

    # with open('transactions_data.pickle', 'w') as data_file:
    # pickle.dump(transactions_data, data_file)

    with open('transactions_data.pickle', 'r') as data_file:
        transactions_data = pickle.load(data_file)

    # govuk_organisations = get_govuk_organisations()

    # with open('govuk_organisations.pickle', 'w') as org_file:
        # pickle.dump(govuk_organisations, org_file)

    with open('govuk_organisations.pickle', 'r') as org_file:
        govuk_organisations = pickle.load(org_file)

    # import json
    # with open('thing.json', 'w') as f:
    # f.write(json.dumps([org for org in govuk_organisations if org['web_url'] == 'https://www.gov.uk/government/organisations/crown-prosecution-service']))  # noqa
    # with open('thing2.json', 'w') as f:
    # f.write(json.dumps([org for org in govuk_organisations if org['web_url'] == 'https://www.gov.uk/government/organisations/attorney-generals-office']))  # noqa
    # with open('thing3.json', 'w') as f:
    # f.write(json.dumps(list(set([org['format'] for org in govuk_organisations]))))  # noqa
    return transactions_data, govuk_organisations


def load_organisations(username, password):
    transactions_data, govuk_organisations = load_data(username, password)

    # remove any orgs from the list from GOV.UK where they have shut down
    govuk_organisations = \
        [org for org in govuk_organisations if org[
            'details']['closed_at'] is None]

    # print transactions_data
    # print govuk_organisations

    nodes_hash = build_up_node_hash(transactions_data, govuk_organisations)
    # as this is recursive internally
    # we could filter to start with the transactions only
    # and then return these created and keyed off the name at the end
    # however I don't fully understand the graph yet and there may be
    # orphans building up in this way.
    # instead ensure we create everything and then load transactions that
    # have been created and associate based on the standard way of building
    # up a transaction name
    create_nodes(nodes_hash)

    finished = []
    bruk = []
    for transaction in transactions_data:
        if associate_with_dashboard(transaction):
            finished.append(transaction)
        else:
            bruk.append(transaction)
    print 'Successfully linked to dashboards'
    print finished
    print len(finished)
    print '^'
    print 'Broken links'
    print bruk
    print len(bruk)
    print '^'


def associate_with_dashboard(transaction_hash):
    transaction = Node.objects.filter(
        name=transaction_name(transaction_hash)).first()
    dashboards = []
    if transaction:
        dashboards = Dashboard.objects.by_tx_id(transaction_hash['tx_id'])
        for dashboard in dashboards:
            # do this even if there is an existing dashboard
            existing_org = dashboard.organisation
            dashboard.organisation = transaction
            dashboard.save()
            # but say if the ancestors do not contain the old one.
            if(existing_org and existing_org not in
               [org for org in dashboard.organisation.get_ancestors()]):
                print("existing org {} for dashboard {}"
                      "not in new ancestors {}".format(
                          existing_org.name,
                          dashboard.title,
                          [org for org
                           in dashboard.organisation.get_ancestors()]))
    print [dashboard for dashboard in dashboards]
    return [dashboard for dashboard in dashboards]


# These may not be 100% accurate however the derived
# typeOf will be overwritten with more certain information
# based on iterating through all tx rows in build_up_node_hash.
# We use this to to get the full org graph with types even when orgs are
# not associated with a transaction in txex. This is the best guess mapping.
types_hash = {
    "Advisory non-departmental public body": 'agency',
    "Tribunal non-departmental public body": 'agency',
    "Sub-organisation": 'agency',
    "Executive agency": 'agency',
    "Devolved administration": 'agency',
    "Ministerial department": 'department',
    "Non-ministerial department": 'department',
    "Executive office": 'agency',
    "Civil Service": 'agency',
    "Other": 'agency',
    "Executive non-departmental public body": 'agency',
    "Independent monitoring body": 'agency',
    "Public corporation": 'agency'
}


def create_nodes(nodes_hash):
    failed_to_create = []
    created = []
    existing = []
    failed_to_find_or_create_parent = defaultdict(list)
    errors = defaultdict(list)

    def _get_or_create_node(node_hash, nodes_hash):
        node_type, _ = NodeType.objects.get_or_create(name=node_hash['typeOf'])
        try:
            node, _ = Node.objects.get_or_create(
                name=node_hash['name'],
                abbreviation=slugify(node_hash['abbreviation']),
                typeOf=node_type
            )
            if _:
                created.append({
                    'name': node_hash['name'],
                    'abbreviation': slugify(node_hash['abbreviation']),
                    'typeOf': node_type
                })
            else:
                existing.append({
                    'name': node_hash['name'],
                    'abbreviation': slugify(node_hash['abbreviation']),
                    'typeOf': node_type
                })
            for parent_id in node_hash['parents']:
                parent = _get_or_create_node(nodes_hash[parent_id], nodes_hash)
                if parent:
                    node.parents.add(parent)
                else:
                    failed_to_find_or_create_parent[node_hash['name']].append(
                        nodes_hash[parent_id])
            return node
        except(django.db.utils.DataError,
               django.db.utils.IntegrityError) as e:
            errors[e.__class__].append(e)
            failed_to_create.append({
                'name': node_hash['name'],
                'abbreviation': slugify(node_hash['abbreviation']),
                'typeOf': node_type
            })

    for key_or_abbr, node_hash in nodes_hash.items():
        _get_or_create_node(node_hash, nodes_hash)

    print 'Created'
    print created
    print len(created)
    print '^'
    print 'Existing'
    print existing
    print len(existing)
    print '^'
    print 'Failed to find or create'
    print failed_to_create
    print len(failed_to_create)
    for error_type, error in errors.items():
        print error_type
        print len(error)
    print '^'
    print 'Failed to find or create parent'
    print failed_to_find_or_create_parent
    print len(failed_to_find_or_create_parent)
    print '^'


def build_up_org_hash(organisations):
    org_id_hash = {}
    # note, typeOf will be overwritten with more certain information
    # based on iterating through all tx rows in build_up_node_hash.
    # We do this here though to to get the full org graph even when orgs are
    # not associated with a transaction in txex
    for org in organisations:
        org_id_hash[org['id']] = {
            'name': org['title'],
            'abbreviation': org['details']['abbreviation'],
            'typeOf': types_hash[org['format']],
            'parents': []
        }

    not_found_orgs = defaultdict(list)

    # assign parents
    for org in organisations:
        for parent in org['parent_organisations']:
            if org_id_hash[parent['id']]:
                abbr = org_id_hash[parent['id']]['abbreviation']
                if abbr:
                    parent_abbreviation = abbr
                elif org_id_hash[parent['id']]['name']:
                    parent_abbreviation = org_id_hash[parent['id']]['name']
            else:
                not_found_orgs[org_id_hash[parent['id']]['abbreviation']] = org

            org_id_hash[org['id']]['parents'].append(
                slugify(parent_abbreviation))

    # now the structure of the gov.uk org graph is replicated,
    # create a new hash keyed off the abbreviation for use in linking
    # to the tx data.
    org_hash = {}
    abbrs_twice = defaultdict(list)
    for org_id, org in org_id_hash.items():
        if slugify(org['abbreviation']) in org_hash:
            # this could be the place for case statements to
            # decide on a better names but for now just record any problems
            if not abbrs_twice[slugify(org['abbreviation'])]:
                abbrs_twice[slugify(org['abbreviation'])].append(
                    org_hash[slugify(org['abbreviation'])])
            abbrs_twice[slugify(org['abbreviation'])].append(
                org)
            print 'Using name as key for:'
            print org
            org_hash[slugify(org['name'])] = org
        else:
            # if there is an abbreviation use it
            # otherwise use the name
            if slugify(org['abbreviation']):
                org_hash[slugify(org['abbreviation'])] = org
            else:
                print org
                org_hash[slugify(org['name'])] = org

    print "No parents found:"
    print not_found_orgs
    print "Duplicate abbreviations - need handling:"
    # 6 problems found.
    print [(abbr, tx) for abbr, tx in abbrs_twice.items()]
    return org_hash


def slugify(string):
    if string:
        return string.lower()
    else:
        return string


def service_name(tx):
    return "{}".format(tx['service']['name'].encode('utf-8'))


def transaction_name(tx):
    return "{}: {}".format(tx['name'].encode('utf-8'),
                           tx['slug'].encode('utf-8'))


def add_type_to_parent(parent, typeOf):
    parent['typeOf'] = typeOf
    return parent


no_agency_found = []
no_dep_found = []


def associate_parents(tx, org_hash, typeOf, rememberer):
    # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
    if slugify(tx[typeOf]['abbr']) in org_hash:
        parent = org_hash[slugify(tx[typeOf]['abbr'])]
        parent = add_type_to_parent(parent, typeOf)
        # prevent null or blank string parents
        if slugify(parent['abbreviation']):
            org_hash[service_name(tx)]['parents'].append(
                slugify(parent['abbreviation']))
        else:
            # This needs to be better and make clear
            # the parent has no name or abbrevation
            # how did it get his way?
            print("This needs to be better and make clear"
                  "the parent has no name or abbrevation"
                  "how did it get his way?")
            rememberer.append(('service', org_hash[service_name(tx)]))
    # try the name if no luck with the abbreviation
    elif slugify(tx[typeOf]['name']) in org_hash:
        parent = org_hash[slugify(tx[typeOf]['name'])]
        parent = add_type_to_parent(parent, typeOf)
        # prevent null or blank string parents
        if slugify(parent['name']):
            org_hash[service_name(tx)]['parents'].append(
                slugify(parent['name']))
        else:
            # This needs to be better and make clear
            # the parent has no name or abbrevation
            # how did it get his way?
            print("This needs to be better and make clear"
                  "the parent has no name or abbrevation"
                  "how did it get his way?")
            rememberer.append(('service', org_hash[service_name(tx)]))
    # if there is nothing for name
    # or abbreviation then add to not found
    else:
        rememberer.append(tx[typeOf])


def build_up_node_hash(transactions, organisations):

    print 'transactions to create:'
    print len(transactions)
    print '^'
    print 'organisations to create:'
    print len(organisations)
    print '^'
    org_hash = build_up_org_hash(organisations)
    more_than_one_tx = []
    more_than_one_service = []
    """
    go through each transaction and build hash with names as keys
    """
    for tx in transactions:
        if transaction_name(tx) in org_hash:
            more_than_one_tx.append(transaction_name(tx))
            # raise Exception('More than one transaction with name {}'.format(
            # transaction_name(tx)))
        if service_name(tx) in org_hash:
            more_than_one_service.append(service_name(tx))
            # raise Exception('More than one service with name {}'.format(
            # service_name(tx)))

        org_hash[transaction_name(tx)] = {
            'name': transaction_name(tx),
            'abbreviation': None,
            'typeOf': 'transaction',
            'parents': [service_name(tx)]
        }
        org_hash[service_name(tx)] = {
            'name': service_name(tx),
            'abbreviation': None,
            'typeOf': 'service',
            'parents': []
        }
    print 'more than one service'
    print more_than_one_service
    print len(more_than_one_service)
    print '^'
    print 'more than one tx'
    print more_than_one_tx
    print len(more_than_one_tx)
    print '^'
    """
    go through again
    """
    for tx in transactions:
        """
        ***THIS IS ASSUMING AGENCIES ARE ALWAYS JUNIOR TO DEPARTMENTS****
        """
        # if there is an agency then get the thing by abbreviation
        if tx["agency"]:
            associate_parents(tx, org_hash, 'agency', no_agency_found)
        # if there is a department and no agency
        elif tx['department']:
            # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
            associate_parents(tx, org_hash, 'department', no_dep_found)
        else:
            raise Exception("transaction with no department or agency!")

    print "No department found:"
    print no_dep_found
    print len(no_dep_found)
    print "No agency found:"
    print len(no_agency_found)
    return org_hash


def main():
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        print "Please supply as environment variables:"
        print "username (GOOGLE_USERNAME)"
        print "password (GOOGLE_PASSWORD)"
        sys.exit(1)

    load_organisations(username, password)


if __name__ == '__main__':
    main()

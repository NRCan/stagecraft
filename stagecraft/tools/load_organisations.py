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

    print transactions_data
    print govuk_organisations

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
    for transaction in transactions_data:
        associate_with_dashboard(transaction)


def associate_with_dashboard(transaction_hash):
    transaction = Node.objects.get(name=transaction_name(transaction_hash))
    dashboards = Dashboard.objects.by_tx_id(transaction_hash['tx_id'])
    for dashboard in dashboards:
        dashboard.organisation = transaction
        dashboard.save()

# a type for all of these or map them? or is there a
# field other than format we should use?
# we may need to map from what they are in tx
types_hash = {
    "Advisory non-departmental public body": 'department',
    "Tribunal non-departmental public body": 'department',
    "Sub-organisation": 'department',
    "Executive agency": 'department',
    "Devolved administration": 'department',
    "Ministerial department": 'department',
    "Non-ministerial department": 'agency',
    "Executive office": 'department',
    "Civil Service": 'department',
    "Other": 'department',
    "Executive non-departmental public body": 'department',
    "Independent monitoring body": 'department',
    "Public corporation": 'department'
}


def create_nodes(nodes_hash):
    def _get_or_create_node(node_hash, nodes_hash):
        node_type, _ = NodeType.objects.get_or_create(name=node_hash['typeOf'])
        node, _ = Node.objects.get_or_create(
            name=node_hash['name'],
            abbreviation=slugify(node_hash['abbreviation']),
            typeOf=node_type
        )
        for parent in node_hash['parents']:
            node.parents.add(
                _get_or_create_node(
                    nodes_hash[parent],
                    nodes_hash))
        return node
    for key_or_abbr, node_hash in nodes_hash.items():
        _get_or_create_node(node_hash, nodes_hash)


def build_up_org_hash(organisations):
    org_id_hash = {}
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
                parent_abbreviation = org_id_hash[parent['id']]['abbreviation']
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
            abbrs_twice[slugify(org['abbreviation'])].append(
                org)
            if not abbrs_twice[slugify(org['abbreviation'])]:
                abbrs_twice[slugify(org['abbreviation'])].append(
                    org_hash[slugify(org['abbreviation'])])
        else:
            org_hash[slugify(org['abbreviation'])] = org

    print "No parents found:"
    print not_found_orgs
    print "Duplicate abbreviations - need handling:"
    print abbrs_twice
    return org_hash


def slugify(string):
    if string:
        return string.lower()
    else:
        return string


def service_name(tx):
    return "{}".format(tx['service']['name'])


def transaction_name(tx):
    return "{}: {}".format(tx['name'], tx['slug'])


def build_up_node_hash(transactions, organisations):

    no_agency_found = []
    no_dep_found = []
    org_hash = build_up_org_hash(organisations)
    """
    go through each transaction and build hash with names as keys
    """
    for tx in transactions:
        if transaction_name(tx) in org_hash:
            raise 'More than one transaction with name {}'.format(
                transaction_name(tx))
        if service_name(tx) in org_hash:
            raise 'More than one transaction with name {}'.format(
                service_name(tx))

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
    """
    go through again
    """
    for tx in transactions:
        """
        ***THIS IS ASSUMING AGENCIES ARE ALWAYS JUNIOR TO DEPARTMENTS****
        """
        # if there is an agency then get the thing by abbreviation
        if tx["agency"]:
            # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
            if slugify(tx['agency']['abbr']) in org_hash:
                agency_parent = org_hash[slugify(tx['agency']['abbr'])]
                org_hash[service_name(tx)]['parents'].append(
                    slugify(agency_parent['abbreviation']))
            # try the name if no luck with the abbreviation
            elif slugify(tx['agency']['name']) in org_hash:
                agency_parent = org_hash[slugify(tx['agency']['name'])]
                org_hash[service_name(tx)]['parents'].append(
                    slugify(agency_parent['name']))
            # if there is nothing for name
            # or abbreviation then add to not found
            else:
                no_agency_found.append(tx)
        # if there is a department and no agency
        elif tx['department']:
            # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
            if slugify(tx['department']['abbr']) in org_hash:
                department_parent = org_hash[slugify(tx['department']['abbr'])]
                org_hash[service_name(tx)]['parents'].append(
                    slugify(department_parent['abbreviation']))
            # try the name if no luck with the abbreviation
            elif slugify(tx['department']['name']) in org_hash:
                agency_parent = org_hash[slugify(tx['department']['name'])]
                org_hash[service_name(tx)]['parents'].append(
                    slugify(agency_parent['name']))
            # if there is nothing for name
            # or abbreviation then add to not found
            else:
                no_dep_found.append(tx)
        else:
            raise "transaction with no deparment or agency!"

    print "No department found:"
    print no_dep_found
    print "No agency found:"
    print no_agency_found
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

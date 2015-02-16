import cPickle as pickle
import pprint
import os
import requests
import sys

from collections import defaultdict
from stagecraft.tools import spreadsheets


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


def add_to_slugs(slugs, things):
    for thing in things:
        slug = thing[0]
        if slug in slugs:
            print '{} exists. offender: {} original: {}'.format(
                slug, thing, slugs[slug])
        else:
            slugs[slug] = thing


def main():
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        print "Please supply as environment variables:"
        print "username (GOOGLE_USERNAME)"
        print "password (GOOGLE_PASSWORD)"
        sys.exit(1)

    #transactions_data = spreadsheets.load(username, password)

    # with open('transactions_data.pickle', 'w') as data_file:
        #pickle.dump(transactions_data, data_file)

    with open('transactions_data.pickle', 'r') as data_file:
        transactions_data = pickle.load(data_file)

    #govuk_organisations = get_govuk_organisations()

    # with open('govuk_organisations.pickle', 'w') as org_file:
        #pickle.dump(govuk_organisations, org_file)

    with open('govuk_organisations.pickle', 'r') as org_file:
        govuk_organisations = pickle.load(org_file)

    govuk_organisations = \
        [org for org in govuk_organisations if org[
            'details']['closed_at'] is None]

    abbrs = defaultdict(list)
    types = defaultdict(list)

    for org in govuk_organisations:
        types[org['format']].append(org)
        abbr = org['details']['abbreviation']
        if abbr:
            abbrs[abbr.lower()].append(org)
        # else:
            # print '{} doesnt have an
            # abbr'.format(unicode(org['title']).encode('ascii','ignore'))

    abbrs = dict(abbrs)
    abbrs_twice = \
        {abbr: abbrs[abbr] for abbr, orgs in abbrs.items() if len(orgs) > 1}

    list_abbrs = abbrs.keys()
    list_abbrs.sort()

    print list_abbrs

    #pprint.pprint(dict(abbrs_twice), width=-1)
    #pprint.pprint(dict(types), width=-1)

    not_found_depts = set()
    not_found_agencies = set()

    for transaction in transactions_data:
        dept_abbr = transaction['department']['abbr']
        if transaction['agency'] is not None:
            agency_abbr = transaction['agency']['abbr']
        else:
            agency_abbr = None

        if dept_abbr:
            dept = abbrs[dept_abbr.lower()]
            if dept is None:
                not_found_depts.add(dept_abbr)

        if agency_abbr:
            agency = abbrs.get(agency_abbr.lower(), None)
            if agency is None:
                agency = abbrs.get(transaction['agency']['name'].lower(), None)
                if agency is None:
                    not_found_agencies.add(
                        (agency_abbr, transaction['agency']['name']))

    print not_found_depts
    print not_found_agencies

    # STUFF FOR EXAMINING SPREADSHEET STUFF

    #transactions = set()
    #services = set()
    #agencies = set()
    #departments = set()

    # for transaction in transactions_data:
    #transactions.add((transaction['slug'], transaction['name']))
    # services.add(
    #(transaction['service']['slug'], transaction['service']['name']))
    # if transaction['agency'] is not None:
    # agencies.add((transaction['agency']['slug'], transaction[
    #'agency']['name'], transaction['agency']['abbr']))
    # departments.add((
    # transaction['department']['slug'],
    # transaction['department']['name'],
    # transaction['department']['abbr']))

    #slugs = dict()
    #add_to_slugs(slugs, transactions)
    #add_to_slugs(slugs, services)
    #add_to_slugs(slugs, agencies)
    #add_to_slugs(slugs, departments)

    # print len(transactions)
    # print len(services)
    # print len(agencies)
    # print len(departments)

    # print len(transactions) + len(services) + len(agencies) + len(departments)
    # print len(slugs)

    # print transactions
    # print services
    # print agencies
    # print departments


if __name__ == '__main__':
    main()

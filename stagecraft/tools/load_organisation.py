import os
import sys

from stagecraft.tools import spreadsheets


def add_to_slugs(slugs, things):
    for thing in things:
        slug = thing[0]
        if slug in slugs:
            print 'ahh {} already in slugs. offender: {} original: {}'.format(slug, thing, slugs[slug])
        else:
            slugs[slug] = thing


def main():
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        print "Please supply username (GOOGLE_USERNAME) and password (GOOGLE_PASSWORD) as environment variables"
        sys.exit(1)

    transactions_data = spreadsheets.load(username, password)

    transactions = set()
    services = set()
    agencies = set()
    departments = set()

    for transaction in transactions_data:
        transactions.add((transaction['slug'], transaction['name']))
        services.add((transaction['service']['slug'], transaction['service']['name']))
        if transaction['agency'] is not None:
            agencies.add((transaction['agency']['slug'], transaction['agency']['name'], transaction['agency']['abbr']))
        departments.add((transaction['department']['slug'], transaction['department']['name'], transaction['department']['abbr']))

    slugs = dict()
    #add_to_slugs(slugs, transactions)
    add_to_slugs(slugs, services)
    add_to_slugs(slugs, agencies)
    add_to_slugs(slugs, departments)

    print len(transactions)
    print len(services)
    print len(agencies)
    print len(departments)

    print len(services) + len(agencies) + len(departments)
    print len(slugs)

    print transactions
    print services
    print agencies
    print departments



if __name__ == '__main__':
    main()

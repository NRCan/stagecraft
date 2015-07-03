import itertools

from stagecraft.tools import get_credentials_or_die
from stagecraft.tools.spreadsheets import SpreadsheetMunger


high_vol_sort_orders = [
    'by-name',
    'by-department',
    'by-total-cost',
    'by-cost-per-transaction',
    'by-digital-takeup',
    'by-transactions-per-year',
]

department_sort_orders = [
    'by-department',
    'by-digital-takeup',
    'by-cost',
    'by-data-coverage',
    'by-transactions-per-year',
]

services_sort_orders = [
    'by-name',
    'by-agency',
    'by-category',
    'by-transactions-per-year',
]


def department_slug(service):
    return service['department']['abbr'].lower().replace(' ', '-')


def collect_departments(services):
    return set([department_slug(service) for service in services])


def enumerate_pages(root, sort_orders):
    pages = []
    for sort_order in sort_orders:
        for direction in ['ascending', 'descending']:
            pages.append('{}/{}/{}'.format(root, sort_order, direction))

    return pages


def flatten(l):
    return list(itertools.chain.from_iterable(l))


def main():
    client_email, private_key = get_credentials_or_die()

    munger = SpreadsheetMunger({
        'names_transaction_name': 11,
        'names_transaction_slug': 12,
        'names_service_name': 9,
        'names_service_slug': 10,
        'names_tx_id': 19,
        'names_other_notes': 17,
        'names_notes': 3,
        'names_description': 8
    })
    services = munger.load(client_email, private_key)

    departments = collect_departments(services)
    pages = \
        enumerate_pages('high-volume-services', high_vol_sort_orders) + \
        enumerate_pages('all-services', department_sort_orders) + \
        flatten([enumerate_pages('department/{}'.format(d), services_sort_orders) for d in departments])

    pages = ['/performance/transactions-explorer/{}'.format(page) for page in pages]

    for page in pages:
        print '{},/performance/services'.format(page)


if __name__ == '__main__':
    main()

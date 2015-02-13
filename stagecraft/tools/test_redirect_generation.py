import os
import json
from .redirects import generate, write
from hamcrest import (
    assert_that, equal_to
)

result_path = 'stagecraft/tools/fixtures/spreadsheet_munging_result.json'
with open(result_path, 'r') as f:
    spreadsheets_data = json.loads(f.read())


def test_redirects_produced():
    redirects = generate(spreadsheets_data)
    assert_that(redirects, equal_to([
        ['source', 'destination'],
        ['/performance/transactions-explorer/service-details/bis-acas-elearning-registrations', '/performance/training-resources-on-workplace-relations/registrations']  # noqa
    ]))


def test_no_redirect_if_no_existing_page():
    try:
        write([['bif', 'bof', 'foo'], ['1', 2], ['va lue', 'another']])
        with open('redirects.csv', 'r') as f:
            assert_that(f.read(), equal_to(
                'bif,bof,foo\r\n1,2\r\nva lue,another\r\n'))
    finally:
        os.remove('redirects.csv')

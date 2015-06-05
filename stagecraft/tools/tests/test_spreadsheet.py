from ..spreadsheets import SpreadsheetMunger
import json

from mock import Mock
from hamcrest import (
    assert_that, has_entries
)


with open('stagecraft/tools/fixtures/tx2.json') as f:
    tx_worksheet = json.loads(f.read())

with open('stagecraft/tools/fixtures/names.json') as f:
    names_worksheet = json.loads(f.read())


def test_merge():

    munger = SpreadsheetMunger({
        'names_transaction_name': 6,
        'names_transaction_slug': 7,
        'names_service_name': 4,
        'names_service_slug': 5,
        'names_tx_id': 16,
        'names_description': 4,
        'names_notes': 4,
        'names_other_notes': 4
    })

    mock_account = Mock()
    mock_account.open_by_key().worksheet(
    ).get_all_values.return_value = tx_worksheet
    tx = munger.load_tx_worksheet(mock_account)

    mock_account = Mock()
    mock_account.open_by_key().worksheet(
    ).get_all_values.return_value = names_worksheet
    names = munger.load_names_worksheet(mock_account)

    result = munger.merge(tx, names)
    result_path = 'stagecraft/tools/fixtures/spreadsheet_munging_result.json'
    with open(result_path, 'r') as f:
        assert_that(result[0], has_entries(json.loads(f.read())[0]))


def test_no_agency_abbr():

    with open('stagecraft/tools/fixtures/tx_no_agency_abbr.json') as f:
        tx_no_abbr_ws = json.loads(f.read())

    munger = SpreadsheetMunger({
        'names_transaction_name': 6,
        'names_transaction_slug': 7,
        'names_service_name': 4,
        'names_service_slug': 5,
        'names_tx_id': 16,
        'names_description': 4,
        'names_notes': 4,
        'names_other_notes': 4
    })

    mock_account = Mock()
    mock_account.open_by_key().worksheet(
    ).get_all_values.return_value = tx_no_abbr_ws
    tx = munger.load_tx_worksheet(mock_account)

    mock_account = Mock()
    mock_account.open_by_key().worksheet(
    ).get_all_values.return_value = names_worksheet
    names = munger.load_names_worksheet(mock_account)

    result = munger.merge(tx, names)
    result_path = 'stagecraft/tools/fixtures/' \
                  'spreadsheet_munging_no_agency_abbr_result.json'
    with open(result_path, 'r') as f:
        assert_that(result[0], has_entries(json.loads(f.read())[0]))

from hamcrest import (
    assert_that, is_not, is_
)
from mock import patch

from stagecraft.apps.dashboards.tests.factories.factories import ModuleFactory
from stagecraft.apps.datasets.tests.factories import DataSetFactory

from ..load_organisations import load_organisations


tx_fixture = [
    {
        'name': '',
        'service': {'name': '', 'slug': ''},
        'agency': None,
        'tx_id': '',
        'department': {
            'slug': 'home office',
            'abbr': 'Home Office',
            'name': 'Home Office'},
        'slug': ''
    }
]

govuk_fixture = [
    {
        'format': u'Ministerial department',
        'title': "Attorney General's Office",
        'details': {
            'slug': 'attorney-generals-office',
            'abbreviation': 'AGO',
            'closed_at': None,
        },
        'parent_organisations': [],
        'child_organisations': [
            {
                'web_url': "https://www.gov.uk/government"
                           "/organisations/treasury-solicitor-s-department",
                'id': "https://www.gov.uk/api/organisations/"
                      "treasury-solicitor-s-department"
            },
            {
                'web_url': "https://www.gov.uk/government/organisations"
                           "/crown-prosecution-service",
                'id': "https://www.gov.uk/api/organisations"
                      "/crown-prosecution-service"
            }
        ]
    },
]


@patch('stagecraft.tools.load_organisations.load_data')
def test_load_organisations(mock_load_data):
    mock_load_data.return_value = tx_fixture, govuk_fixture

    tx_data_set = DataSetFactory(
        name='transactional_services_summaries',
    )
    kpi_module = ModuleFactory(
        data_set=tx_data_set,
        query_parameters={
            'filter_by': ['service_id:daa-reports-filing'],
        }
    )
    dashboard = kpi_module.dashboard

    load_organisations('foo', 'bar')

    assert_that(dashboard.organisation, is_not(None))

    org_parents = dashboard.organisation.get_ancestors(include_self=True)

    assert_that(len(org_parents), is_(4))
    assert_that(org_parents[0].name, is_('Report filing'))
    assert_that(org_parents[0].typeOf.name, is_('transaction'))
    assert_that(org_parents[1].name, is_('Filing cabinet service'))
    assert_that(org_parents[1].typeOf.name, is_('service'))
    assert_that(org_parents[2].name, is_('Paper love agency'))
    assert_that(org_parents[2].typeOf.name, is_('agency'))
    assert_that(org_parents[3].name, is_(
        'Department of Administrative Affairs'))
    assert_that(org_parents[3].typeOf.name, is_('department'))

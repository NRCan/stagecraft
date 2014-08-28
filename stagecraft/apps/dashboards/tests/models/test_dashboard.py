from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase
from hamcrest import (
    assert_that, has_entry, has_key, is_not, has_length, equal_to, instance_of,
    has_entries, has_items, is_not, has_property, is_, none, calling, raises,
    starts_with
)
from nose.tools import eq_, assert_raises

from ...models import Dashboard, Link
from ....organisation.models import Node, NodeType
import factory



class DashboardTestCase(TransactionTestCase):

    def setUp(self):
        self.dashboard = Dashboard.objects.create(
            published=True,
            title="title",
            slug="slug"
        )

    def test_transaction_link(self):
        self.dashboard.update_transaction_link('blah', 'http://www.gov.uk')
        self.dashboard.update_transaction_link('blah2', 'http://www.gov.uk')
        self.dashboard.validate_and_save()
        assert_that(self.dashboard.link_set.all(), has_length(1))
        assert_that(self.dashboard.link_set.first().title, equal_to('blah2'))
        assert_that(
            self.dashboard.link_set.first().link_type,
            equal_to('transaction')
        )

    def test_other_link(self):
        self.dashboard.add_other_link('blah', 'http://www.gov.uk')
        self.dashboard.add_other_link('blah2', 'http://www.gov.uk')
        self.dashboard.validate_and_save()
        links = self.dashboard.link_set.all()

        assert_that(links, has_length(2))
        assert_that(
            links,
            has_items(
                has_property('title', 'blah'),
                has_property('title', 'blah2'),
            )
        )
        assert_that(
            self.dashboard.link_set.first().link_type,
            equal_to('other')
        )

    def test_other_and_transaction_link(self):
        self.dashboard.add_other_link('other', 'http://www.gov.uk')
        self.dashboard.add_other_link('other2', 'http://www.gov.uk')
        self.dashboard.update_transaction_link(
            'transaction',
            'http://www.gov.uk'
        )
        self.dashboard.validate_and_save()
        transaction_link = self.dashboard.get_transaction_link()
        assert_that(transaction_link, instance_of(Link))
        assert_that(
            transaction_link.link_type,
            equal_to('transaction')
        )
        assert_that(
            self.dashboard.get_other_links()[0].link_type,
            equal_to('other')
        )
        assert_that(
            self.dashboard.serialize(),
            has_entries({
                'title': 'title',
                'page-type': 'dashboard',
                'relatedPages': has_entries({
                    'improve-dashboard-message': True,
                    'transaction_link':
                    has_entries({
                        'url': 'http://www.gov.uk',
                        'title': 'transaction',
                        }),
                    'other_links':
                    has_items(
                        has_entries({
                            'url': 'http://www.gov.uk',
                            'title': 'other',
                        }),
                        has_entries({
                            'url': 'http://www.gov.uk',
                            'title': 'other2',
                        }),
                    )
                })
            })
        )

        assert_that(self.dashboard.serialize(), is_not(has_key('id')))
        assert_that(self.dashboard.serialize(), is_not(has_key('link')))

    def test_dashboard_without_transaction_link_will_serialize(self):
        assert_that(
            self.dashboard.serialize(), has_entries({'title': 'title'}))

    def test_department(self):
        # dashboard = DashboardFactory()
        # node = NodeFactory()
        department_type = NodeType.objects.create(
            name='department'
        )
        department = Node.objects.create(
            name='department-node',
            typeOf=department_type
        )
        department.save()
        agency_type = NodeType.objects.create(
            name='agency'
        )
        agency = Node.objects.create(
            name='agency-node',
            typeOf=agency_type,
            parent=department
        )

        self.dashboard.organisation = agency
        self.dashboard.validate_and_save()
        assert_that(
            self.dashboard.serialize(),
            has_entry(
                'department',
                has_entries({
                    'title': starts_with('department'),
                    'abbr': starts_with('department')
                })
            )
        )
        assert_that(
            self.dashboard.serialize(),
            has_entry(
                'agency',
                has_entries({
                    'title': starts_with('agency'),
                    'abbr': starts_with('agency')
                })
            )
        )

    def test_agency_returns_none_when_no_organisation(self):
        assert_that(self.dashboard.agency(), is_(none()))

    def test_agency_returns_none_when_organisation_is_a_department(self):
        self.dashboard.organisation = DepartmentFactory()
        self.dashboard.save()

        assert_that(self.dashboard.agency(), is_(none()))

    def test_agency_returns_organisation_when_organisation_is_an_agency(self):
        agency = AgencyFactory()
        self.dashboard.organisation = agency
        assert_that(self.dashboard.agency(), equal_to(agency))

    def test_department_returns_organisation_when_organisation_is_a_department(self):
        self.dashboard.organisation = DepartmentFactory()
        assert_that(
            self.dashboard.department(), equal_to(self.dashboard.organisation))

    def test_department_returns_agency_department_when_organisation_is_an_agency(self):
        agency = AgencyWithDepartmentFactory()
        self.dashboard.organisation = agency
        assert_that(self.dashboard.department(), equal_to(agency.parent))

    def test_department_throws_exception_when_agency_has_no_department(self):
        self.dashboard.organisation = AgencyFactory()
        assert_that(calling(self.dashboard.department), raises(ValueError))

    def test_department_returns_none_when_organisation_is_none(self):
        assert_that(self.dashboard.department(), is_(none()))

    def create_department(self):
        department_type = NodeType.objects.create(
            name='department'
        )
        department = Node.objects.create(
            name='department-node',
            typeOf=department_type
        )
        department.save()
        return department

    def create_agency(self):
        agency_type = NodeType.objects.create(
            name='agency'
        )
        agency = Node.objects.create(
            name='agency-node',
            typeOf=agency_type
        )
        agency.save()
        return agency



class DashboardFactory(factory.DjangoModelFactory):
    class Meta:
        model = Dashboard

    published = True,
    title = "title",
    slug = factory.Sequence(lambda n: 'slug%s' % n)


class NodeTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = NodeType


class DepartmentTypeFactory(NodeTypeFactory):
    name = 'department'


class AgencyTypeFactory(NodeTypeFactory):
    name = 'agency'


class NodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = Node
    name = factory.Sequence(lambda n: 'name-%s' % n)
    abbreviation = factory.Sequence(lambda n: 'abbreviation-%s' % n)
    typeOf = factory.SubFactory(NodeTypeFactory)


class DepartmentFactory(NodeFactory):
    name = factory.Sequence(lambda n: 'department-%s' % n)
    typeOf = factory.SubFactory(DepartmentTypeFactory)


class AgencyFactory(NodeFactory):
    name = factory.Sequence(lambda n: 'agency-%s' % n)
    typeOf = factory.SubFactory(AgencyTypeFactory)


class AgencyWithDepartmentFactory(AgencyFactory):
    parent = factory.SubFactory(DepartmentFactory)

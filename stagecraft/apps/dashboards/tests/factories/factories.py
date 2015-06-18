import factory

from ...models import Dashboard, Link, ModuleType, Module
from ....users.models import User
from ....organisation.tests.factories import NodeFactory, NodeTypeFactory


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User


class DashboardFactory(factory.DjangoModelFactory):

    class Meta:
        model = Dashboard

    status = 'published'
    title = "title"
    slug = factory.Sequence(lambda n: 'slug%s' % n)


class DashboardWithOwnerFactory(DashboardFactory):
    @factory.post_generation
    def owners(self, create, extracted, **kwargs):
        if create:
            for owner in extracted:
                self.owners.add(owner)


class LinkFactory(factory.DjangoModelFactory):

    class Meta:
        model = Link

    url = factory.Sequence(lambda n: 'https://www.gov.uk/link-%s' % n)
    title = 'Link title'
    link_type = 'transaction'
    dashboard = factory.SubFactory(DashboardFactory)


class ModuleTypeFactory(factory.DjangoModelFactory):

    class Meta:
        model = ModuleType

    name = factory.Sequence(lambda n: 'name %s' % n)
    schema = {}


class ModuleFactory(factory.DjangoModelFactory):

    class Meta:
        model = Module

    type = factory.SubFactory(ModuleTypeFactory)
    dashboard = factory.SubFactory(DashboardFactory)
    slug = factory.Sequence(lambda n: 'slug{}'.format(n))
    title = 'title'
    info = []
    options = {}
    order = factory.Sequence(lambda n: n)


class DepartmentTypeFactory(NodeTypeFactory):
    name = 'department'


class AgencyTypeFactory(NodeTypeFactory):
    name = 'agency'


class ServiceTypeFactory(NodeTypeFactory):
    name = 'service'


class DepartmentFactory(NodeFactory):
    name = factory.Sequence(lambda n: 'department-%s' % n)
    typeOf = factory.SubFactory(DepartmentTypeFactory)


class AgencyFactory(NodeFactory):
    name = factory.Sequence(lambda n: 'agency-%s' % n)
    typeOf = factory.SubFactory(AgencyTypeFactory)


class AgencyWithDepartmentFactory(AgencyFactory):
    parent = factory.SubFactory(DepartmentFactory)


class ServiceFactory(NodeFactory):
    parent = factory.SubFactory(AgencyWithDepartmentFactory)
    name = factory.Sequence(lambda n: 'service-%s' % n)
    typeOf = factory.SubFactory(ServiceTypeFactory)

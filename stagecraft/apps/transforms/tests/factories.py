import factory

from ..models import TransformType, Transform
from ...datasets.tests.factories import DataTypeFactory


class TransformTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = TransformType

    name = factory.Sequence(lambda n: 'name %s' % n)
    function = factory.Sequence(lambda n: 'function.%s' % n)
    schema = {}


class TransformFactory(factory.DjangoModelFactory):
    class Meta:
        model = Transform

    type = factory.SubFactory(TransformTypeFactory)
    input_type = factory.SubFactory(DataTypeFactory)
    output_type = factory.SubFactory(DataTypeFactory)
    query_parameters = {}
    options = {}

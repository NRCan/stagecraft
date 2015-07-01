import json
from unittest import TestCase

from hamcrest import (
    assert_that, is_, calling, raises, is_not,
    instance_of, starts_with, has_key, has_entry,
    contains, equal_to)

from ..schema import output
from stagecraft.apps.organisation.views import (
    NodeView, NodeTypeView)


class SchemaTestCase(TestCase):

    def test_output(self):
        combined = output([
            ('node', NodeView),
            ('node-type', NodeTypeView),
        ])

        print json.dumps(combined, indent=2)

        assert_that(combined, is_('foo'))

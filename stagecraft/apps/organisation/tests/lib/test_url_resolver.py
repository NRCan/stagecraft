from django.test import TestCase
from hamcrest import (
    assert_that, equal_to
)


class UrlResolverTestCase(TestCase):

    def test_resolves_a_dashboard_for_a_transaction(self):
        assert_that(False, equal_to(True))
        pass

    def test_resolves_a_dashboard_for_a_service(self):
        pass

    def test_resolves_a_dashboard_for_a_department(self):
        pass

    def test_resolves_a_dashboard_for_a_agency(self):
        pass

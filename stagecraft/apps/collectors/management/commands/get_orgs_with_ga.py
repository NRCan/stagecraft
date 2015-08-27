from django.core.management.base import BaseCommand
from stagecraft.apps.collectors.lib.collectors_to_orgs_with_ga_list import get_list_of_orgs_with_ga  # noqa


class Command(BaseCommand):
    def handle(self, *args, **options):
        get_list_of_orgs_with_ga()

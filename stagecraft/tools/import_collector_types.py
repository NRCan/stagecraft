import os
import json
from django.db import IntegrityError
from stagecraft.apps.collectors.models import CollectorType, Provider


def create_collector_types():

    schema_dir = "stagecraft/apps/collectors/schemas"

    for collector_type_name in os.listdir(schema_dir):
        collector_type_dir = schema_dir + "/" + collector_type_name

        if os.path.isdir(collector_type_dir):
            query_schema = open(collector_type_dir + "/query.json").read()
            options_schema = open(collector_type_dir + "/options.json").read()
            collector_type_schema = open(
                collector_type_dir + "/descriptor.json").read()

            collector_type_dict = json.loads(collector_type_schema)
            provider_name = collector_type_name.split('-')[0]
            entry_point = "performanceplatform.collector." + \
                          collector_type_name.replace("-", ".")

            provider, _ = Provider.objects.get_or_create(name=provider_name)

            try:
                CollectorType.objects.create(name=collector_type_dict["title"],
                                             slug=collector_type_name,
                                             provider=provider,
                                             entry_point=entry_point,
                                             query_schema=query_schema,
                                             options_schema=options_schema)
            except IntegrityError:
                continue


if __name__ == "__main__":
    create_collector_types()

import itertools

from copy import deepcopy

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from .resource import registered_resources
from .utils import to_json


def flatten(arr):
    return list(itertools.chain.from_iterable(arr))


def output(roots_and_resources):
    resources = set([r for (_, r) in roots_and_resources])
    linked_resources = set(flatten([[sr.__class__ for sr in r.sub_resources.values()] for r in resources]))
    missing_resources = linked_resources.difference(resources)

    if len(missing_resources) > 0:
        print 'Missing resources: {}'.format(missing_resources)
        return None

    definitions = {}

    for root, resource in roots_and_resources:
        name = resource.model.__name__
        schema = deepcopy(resource.schema['out'])

        # add identity definition based on id_fields
        schema['definitions'] = {
            'identity': {
                'anyOf': [{'$ref': '#/definitions/{}/properties/{}'.format(name, id_field)} for id_field in resource.id_fields],
            },
        }

        # base set of links from resource
        links = [
            {
                'title': 'Get',
                'description': 'Get by id',
                'href': '/{}/{{(#/definitions/{}/definitions/identity)}}'.format(root, name),
                'method': 'GET',
                'rel': 'self',
                'targetSchema': {
                    #'$ref': '#/definitions/{}'.format(name),
                },
            },
            {
                'title': 'List',
                'description': 'List the things',
                'href': '/{}'.format(root),
                'method': 'GET',
                'rel': 'instances',
                'targetSchema': {
                    'items': {
                        #'$ref': '#/definitions/{}'.format(name),
                    },
                    'type': 'array',
                },
            },
            {
                'title': 'Create',
                'description': 'Create a thing',
                'href': '/{}'.format(root),
                'method': 'POST',
                'rel': 'create',
                'schema': resource.schema['in'],
                'targetSchema': {
                    #'$ref': '#/definitions/{}'.format(name),
                },
            },
            {
                'title': 'Update',
                'description': 'Update a thing',
                'href': '/{}/{{(#/definitions/{}/definitions/identity)}}'.format(root, name),
                'method': 'PUT',
                'rel': 'update',
                'schema': resource.schema['in'],
                'targetSchema': {
                    #'$ref': '#/definitions/{}'.format(name),
                },
            },
            {
                'title': 'Delete',
                'description': 'Delete a thing',
                'href': '/{}/{{(#/definitions/{}/definitions/identity)}}'.format(root, name),
                'method': 'DELETE',
                'rel': 'destroy',
                'targetSchema': {
                    #'$ref': '#/definitions/{}'.format(name),
                },
            },
        ]

        # sub resource links

        schema['links'] = links

        definitions[name] = schema

    return {
        '$schema': 'http://interagent.github.io/interagent-hyper-schema',
        'title': 'Performance Platform API',
        'description': 'An API to interact with the Performance Platform',
        'type': ['object'],
        'links': [{
            'href': settings.APP_ROOT,
            'rel': 'self',
        }, {
            'href': '/schema',
            'method': 'GET',
            'rel': 'self',
            'targetSchema': {
                'additionalProperties': True,
            },
        }],
        'definitions': definitions,
        'properties': {
            name: { '$ref': '#/definitions/' + name }
         for name in definitions},
    }


@require_http_methods(["GET"])
def view(request):
    return HttpResponse(
        to_json(output(registered_resources)),
        content_type='application/json')

from stagecraft.apps.datasets.models import DataGroup, DataType
from .models import Transform, TransformType

from stagecraft.libs.views.resource import ResourceView
from stagecraft.libs.views.utils import create_http_error


def resolve_data_reference(reference):
    if 'data-group' in reference:
        try:
            data_group = DataGroup.objects.get(name=reference['data-group'])
        except DataGroup.DoesNotExist:
            data_group = None
    else:
        data_group = None

    if 'data-type' in reference:
        try:
            data_type = DataType.objects.get(name=reference['data-type'])
        except DataType.DoesNotExist:
            data_type = None
    else:
        data_type = None

    return data_group, data_type


class TransformTypeView(ResourceView):

    model = TransformType
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "function": {
                "type": "string",
                "format": "function_name",
            },
            "schema": {
                "type": "object",
            }
        },
        "required": ["name", "function", "schema"],
        "additionalProperties": False,
    }

    def update_model(self, model, model_json, request, parent):
        model.name = model_json['name']
        model.function = model_json['function']
        model.schema = model_json['schema']

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'name': model.name,
            'schema': model.schema,
            'function': model.function,
        }


class TransformView(ResourceView):

    model = Transform
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "type_id": {
                "type": "string",
                "format": "uuid",
            },
            "input": {
                "type": "object",
                "properties": {
                    "data-group": {
                        "type": "string",
                        "format": "slug",
                    },
                    "data-type": {
                        "type": "string",
                        "format": "slug",
                    },
                },
                "required": ["data-type"],
                "additionalProperties": False,
            },
            "query-parameters": {
                "type": "object",
            },
            "options": {
                "type": "object",
            },
            "output": {
                "type": "object",
                "properties": {
                    "data-group": {
                        "type": "string",
                        "format": "slug",
                    },
                    "data-type": {
                        "type": "string",
                        "format": "slug",
                    },
                },
                "required": ["data-type"],
                "additionalProperties": False,
            },
        },
        "required": [
            "type_id", "input", "query-parameters",
            "options", "output"
        ],
        "additionalProperties": False,
    }

    def update_model(self, model, model_json, request, parent):
        try:
            transform_type = TransformType.objects.get(
                id=model_json['type_id'])
        except TransformType.DoesNotExist:
            return create_http_error(400, 'transform type was not found',
                                     request)

        (input_group, input_type) = resolve_data_reference(model_json['input'])

        if input_type is None:
            return create_http_error(
                400,
                'input requires at least a data-type (that exists)',
                request)

        (output_group, output_type) = \
            resolve_data_reference(model_json['output'])

        if output_type is None:
            return create_http_error(
                400,
                'output requires at least a data-type (that exists)',
                request)

        model.type = transform_type
        model.input_group = input_group
        model.input_type = input_type
        model.query_parameters = model_json['query-parameters']
        model.options = model_json['options']
        model.output_group = output_group
        model.output_type = output_type

        return None

    @staticmethod
    def serialize(model):
        out = {
            'id': str(model.id),
            'type': {
                'id': str(model.type.id),
                'function': model.type.function,
            },
            'input': {
                'data-type': model.input_type.name,
            },
            'query-parameters': model.query_parameters,
            'options': model.options,
            'output': {
                'data-type': model.output_type.name,
            }
        }

        if model.input_group is not None:
            out['input']['data-group'] = model.input_group.name
        if model.output_group is not None:
            out['output']['data-group'] = model.output_group.name

        return out

# import json
import logging

from django.conf import settings
# from django.core.exceptions import ValidationError
# from django.core.urlresolvers import reverse
# from django.db import IntegrityError
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseNotFound)
# from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control, never_cache
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
from django.views.decorators.vary import vary_on_headers

from stagecraft.apps.dashboards.models.dashboard import Dashboard
from stagecraft.apps.dashboards.views.module import ModuleView
from stagecraft.apps.organisation.models import Node
from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.validation.validation import is_uuid
from stagecraft.libs.views.resource import ResourceView, UUID_RE_STRING
from stagecraft.libs.views.utils import to_json, create_error
# from stagecraft.libs.views.transaction import atomic_view
from .module import add_module_to_dashboard
# from ..models.module import Module
import time

logger = logging.getLogger(__name__)


def dashboards_for_spotlight(request):
    dashboard_slug = request.GET.get('slug')
    if not dashboard_slug:
        return dashboard_list_for_spotlight()
    else:
        return single_dashboard_for_spotlight(request, dashboard_slug)


def dashboard_list_for_spotlight():
    dashboard_json = Dashboard.list_for_spotlight()
    json_str = to_json(dashboard_json)
    response = HttpResponse(json_str, content_type='application/json')
    response['Cache-Control'] = 'max-age=300'
    return response


def single_dashboard_for_spotlight(request, dashboard_slug):
    start = time.time()
    logger.info('fetching dashboard')
    dashboard = fetch_dashboard(dashboard_slug)
    fetch_time = time.time()
    fetch_elapsed = fetch_time - start
    logger.info('fetching dashboard took {}'.format(
        fetch_elapsed), extra={'elapsed_time': fetch_elapsed})
    if not dashboard:
        return error_response(request, dashboard_slug)
    dashboard_json = dashboard.spotlightify(dashboard_slug)
    spotlightify_time = time.time()
    spotlightify_elapsed = spotlightify_time - start
    logger.info('spotlightifying dashboard took {}'.format(
        spotlightify_elapsed), extra={'elapsed_time': spotlightify_elapsed})
    if not dashboard_json:
        return error_response(request, dashboard_slug)
    json_str = to_json(dashboard_json)

    response = HttpResponse(json_str, content_type='application/json')

    response['Access-Control-Allow-Origin'] = '*'

    if dashboard.published:
        response['Cache-Control'] = 'max-age=300'
    else:
        response['Cache-Control'] = 'no-cache'

    return response


def error_response(request, dashboard_slug):
    error = {
        'status': 'error',
        'message': "No dashboard with slug '{}' exists".format(
            dashboard_slug)
    }
    logger.warn(error)
    error["errors"] = [create_error(request, 404, detail=error['message'])]
    return HttpResponseNotFound(to_json(error),
                                content_type='application/json')


def fetch_dashboard(dashboard_slug):
    slug = dashboard_slug.split('/')[0]
    dashboard = Dashboard.objects.filter(slug=slug).first()
    return dashboard


# @cache_control(max_age=60)
# @csrf_exempt
# @require_http_methods(['GET'])
# @permission_required('dashboard')
# def list_dashboards(user, request):
#     parsed_dashboards = []
#
#     for item in Dashboard.objects.all().order_by('title'):
#         parsed_dashboards.append({
#             'id': item.id,
#             'title': item.title,
#             'url': '{0}{1}'.format(
#                 settings.APP_ROOT,
#                 reverse('dashboard', kwargs={'identifier': item.slug})),
#             'public-url': '{0}/performance/{1}'.format(
#                 settings.GOVUK_ROOT, item.slug),
#             'status': item.status,
#             'published': item.published
#         })
#
#     return HttpResponse(to_json({'dashboards': parsed_dashboards}))


# @csrf_exempt
# @require_http_methods(['GET'])
# @permission_required('dashboard')
# def get_dashboard_by_slug(user, request, slug=None):
#     dashboard = get_object_or_404(Dashboard, slug=slug)
#
#     return HttpResponse(
#         to_json(dashboard.serialize()),
#         content_type='application/json'
#     )
#
#
# @csrf_exempt
# @require_http_methods(['GET'])
# @permission_required('dashboard')
# def get_dashboard_by_uuid(user, request, dashboard_id=None):
#     dashboard = get_object_or_404(Dashboard, id=dashboard_id)
#
#     return HttpResponse(
#         to_json(dashboard.serialize()),
#         content_type='application/json'
#     )


# @csrf_exempt
# @require_http_methods(['POST', 'PUT', 'GET'])
# @permission_required('dashboard')
# @never_cache
# @atomic_view
# def dashboard(user, request, identifier=None):
#
#     def add_module_and_children_to_dashboard(dashboard,
#                                              module_data,
#                                              parent=None):
#         modules = []
#         module = add_module_to_dashboard(dashboard, module_data, parent)
#         modules.append(module)
#         for module_data in module_data['modules']:
#             modules.extend(add_module_and_children_to_dashboard(
#                 dashboard, module_data, module))
#         return modules
#
#     if request.method == 'GET':
#         if is_uuid(identifier):
#             return get_dashboard_by_uuid(request, identifier)
#         else:
#             return get_dashboard_by_slug(request, identifier)
#
#     data = json.loads(request.body)
#
# create a dashboard if we don't already have a dashboard slug
#     if identifier is None and request.method == 'POST':
#         dashboard = Dashboard()
#     else:
#         if is_uuid(identifier):
#             dashboard = get_object_or_404(Dashboard, id=identifier)
#         else:
#             dashboard = get_object_or_404(Dashboard, slug=identifier)
#
#     if data.get('organisation'):
#         if not is_uuid(data['organisation']):
#             error = {
#                 'status': 'error',
#                 'message': 'Organisation must be a valid UUID',
#                 'errors': [create_error(
#                     request, 400,
#                     detail='Organisation must be a valid UUID'
#                 )],
#             }
#             return HttpResponseBadRequest(to_json(error))
#
#         try:
#             organisation = Node.objects.get(id=data['organisation'])
#             dashboard.organisation = organisation
#         except Node.DoesNotExist:
#             error = {
#                 'status': 'error',
#                 'message': 'Organisation does not exist',
#                 'errors': [create_error(request, 404,
#                                         detail=
# 'Organisation does not exist')]
#             }
#             return HttpResponseBadRequest(to_json(error))
#
#     for key, value in data.iteritems():
#         if key not in ['organisation', 'links']:
#             setattr(dashboard, key.replace('-', '_'), value)
#
#     try:
#         dashboard.full_clean()
#     except ValidationError as error_details:
#         errors = error_details.message_dict
#         error_list = ['{0}: {1}'.format(field, ', '.join(errors[field]))
#                       for field in errors]
#         formatted_errors = ', '.join(error_list)
#         error = {
#             'status': 'error',
#             'message': formatted_errors,
#             'errors': [create_error(request, 400, title='validation error',
#                                     detail=e)
#                        for e in error_list]
#         }
#         return HttpResponseBadRequest(to_json(error))
#
#     try:
#         dashboard.save()
#     except IntegrityError as e:
#         error = {
#             'status': 'error',
#             'message': '{0}'.format(e.message),
#             'errors': [create_error(request, 400, title='integrity error',
#                                     detail=e.message)]
#         }
#         return HttpResponseBadRequest(to_json(error))
#
#     if 'links' in data:
#         for link_data in data['links']:
#             if link_data['type'] == 'transaction':
#                 link, _ = dashboard.link_set.get_or_create(
#                     link_type='transaction')
#                 link.url = link_data['url']
#                 link.title = link_data['title']
#                 link.save()
#             else:
#                 dashboard.link_set.create(link_type=link_data.pop('type'),
#                                           **link_data)
#
#     if 'modules' in data:
#         module_ids = set([m.id for m in dashboard.module_set.all()])
#
#         for module_data in data['modules']:
#             try:
#                 modules = add_module_and_children_to_dashboard(
#                     dashboard, module_data)
#                 for m in modules:
#                     module_ids.discard(m.id)
#             except ValueError as e:
#                 error = {
#                     'status': 'error',
#                     'message': e.message,
#                     'errors': [create_error(request, 400,
#                                             detail=e.message)]
#                 }
#                 return HttpResponseBadRequest(to_json(error))
#
#         Module.objects.filter(id__in=module_ids).delete()
#
#     return HttpResponse(to_json(dashboard.serialize()),
#                         content_type='application/json')


class DashboardView(ResourceView):
    model = Dashboard

    id_fields = {
        'id': UUID_RE_STRING,
        'slug': '[\w-]+',
    }

    order_by = "title"

    sub_resources = {
        'module': ModuleView(),
    }

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "objects": {
                "type": "string",
            },
            "slug": {
                "type": "string",
            },
            "dashboard_type": {
                "type": "string",
            },
            "page_type": {
                "type": "string",
            },
            "title": {
                "type": "string",
            },
            "description": {
                "type": "string",
            },
            "description_extra": {
                "type": "string",
            },
            "costs": {
                "type": "string",
            },
            "other_notes": {
                "type": "string",
            },
            "customer_type": {
                "type": "string",
            },
            "business_model": {
                "type": "string",
            },
            "improve_dashboard_message": {
                "type": "boolean",
            },
            "strapline": {
                "type": "string",
            },
            "tagline": {
                "type": "string",
            },
            "organisation": {
                "anyOf": [
                    {
                        "type": "string",
                        "format": "uuid"
                    },
                    {"type": "null"},
                ]
            },
            "published": {
                "type": "boolean",
            },
            "links": {
                "type": "array",
            },
            "modules": {
                "type": "array",
            },
            "status": {
                "type": "string",
            },
            "id": {
                "type": "string",
            }
        },
        "required": ["slug", "title"],
        "additionalProperties": True,
    }

    list_filters = {
        'id': 'id__iexact',
        'slug': 'slug_iexact'
    }

    @method_decorator(never_cache)
    def get(self, request, **kwargs):
        return super(DashboardView, self).get(request, **kwargs)

    @method_decorator(permission_required('dashboard'))
    def post(self, user, request, **kwargs):
        return super(DashboardView, self).post(user, request, **kwargs)

    @method_decorator(permission_required('dashboard'))
    @method_decorator(vary_on_headers('Authorization'))
    def put(self, user, request, **kwargs):
        return super(DashboardView, self).put(user, request, **kwargs)

    def update_model(self, model, model_json, request):

        if model_json.get('organisation'):
            org_id = model_json['organisation']
            if not is_uuid(org_id):
                error = {
                    'status': 'error',
                    'message': 'Organisation must be a valid UUID',
                    'errors': [create_error(
                        request, 400,
                        detail='Organisation must be a valid UUID'
                    )],
                }
                return HttpResponseBadRequest(to_json(error))

            try:
                organisation = Node.objects.get(id=org_id)
                model.organisation = organisation
            except Node.DoesNotExist:
                error = {
                    'status': 'error',
                    'message': 'Organisation does not exist',
                    'errors': [
                        create_error(
                            request,
                            404,
                            detail='Organisation does not exist'
                        )
                    ]
                }
                return HttpResponseBadRequest(to_json(error))

        for key, value in model_json.iteritems():
            if key not in ['organisation', 'links']:
                setattr(model, key.replace('-', '_'), value)


    def update_module(self, dashboard, module, parent=None):
        module_model = add_module_to_dashboard(dashboard, module, parent)
        modules = [module_model]

        for child_module in module['modules']:
            modules.extend(
                self.update_module(dashboard, child_module, module_model))

        return modules


    def update_relationships(self, model, model_json, request):
        if 'links' in model_json:
            for link_data in model_json['links']:
                if link_data['type'] == 'transaction':
                    link, _ = model.link_set.get_or_create(
                        link_type='transaction')
                    link.url = link_data['url']
                    link.title = link_data['title']
                    link.save()
                else:
                    model.link_set.create(link_type=link_data.pop('type'),
                                          **link_data)

        if 'modules' in model_json:
            current_module_ids = set([m.id for m in model.module_set.all()])

            for module in model_json['modules']:
                try:
                    for changed_module in self.update_module(model, module):
                        current_module_ids.discard(changed_module.id)
                except ValueError as e:
                    return HttpResponse(e.message, status=400)

            model.module_set.filter(id__in=current_module_ids).delete()


    @staticmethod
    def serialize_for_list(model):
        return {
            'id': str(model.id),
            'title': model.title,
            'url': '{0}/dashboard/{1}'.format(
                settings.APP_ROOT, model.slug),
            'public-url': '{0}/performance/{1}'.format(
                settings.GOVUK_ROOT, model.slug),
            'status': model.status,
            'published': model.published
        }

    @staticmethod
    def serialize(model):
        serialized_data = {
            "id": str(model.id),
            "description_extra": model.description_extra,
            "strapline": model.strapline,
            "description": model.description,
            "title": model.title,
            "tagline": model.tagline,
            "modules": [m.serialize() for m in model.module_set.filter(
                parent=None).order_by('order')],
            "dashboard_type": model.dashboard_type,
            "slug": model.slug,
            "improve_dashboard_message": model.improve_dashboard_message,
            "customer_type": model.customer_type,
            "costs": model.costs,
            "page_type": model.page_type,
            "published": model.published,
            "business_model": model.business_model,
            "other_notes": model.other_notes
        }
        if model.organisation:
            serialized_data["organisation"] = str(model.organisation.id)

        if model.link_set:
            links = []
            if model.get_transaction_link():
                links.append(model.get_transaction_link().serialize())
            if model.get_other_links():
                links.append(model.get_other_links().serialize())
            serialized_data["links"] = links

        return serialized_data

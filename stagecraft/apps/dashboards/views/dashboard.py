import json
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseNotFound)
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from stagecraft.apps.dashboards.models.dashboard import Dashboard
from stagecraft.apps.organisation.models import Node
from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.validation.validation import is_uuid
from stagecraft.libs.views.utils import to_json, create_error
from stagecraft.libs.views.transaction import atomic_view
from .module import add_module_to_dashboard
from ..models.module import Module
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


def single_dashboard_for_spotlight(request, path):
    start = time.time()
    logger.info('fetching dashboard')
    dashboard = fetch_dashboard(path)
    dashboard_slug = '/'.join(path.split('/')[1:])
    fetch_time = time.time()
    fetch_elapsed = fetch_time - start
    logger.info('fetching dashboard took {}'.format(
        fetch_elapsed), extra={'elapsed_time': fetch_elapsed})
    if not dashboard:
        return error_response(request, path)
    dashboard_json = dashboard.spotlightify(dashboard_slug)
    spotlightify_time = time.time()
    spotlightify_elapsed = spotlightify_time - start
    logger.info('spotlightifying dashboard took {}'.format(
        spotlightify_elapsed), extra={'elapsed_time': spotlightify_elapsed})
    if not dashboard_json:
        return error_response(request, path)
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


FETCH_TYPES = set(['services', 'web-traffic', 'dashboard'])
ROOT_NODE_TYPES = set(['department', 'agency', 'service-group'])
TYPE_TO_TYPE = {
    'services': ['transaction', 'high-volume-transaction', 'other', 'service-group'],
    'web-traffic': ['content'],
}


def resolve_node(slugs):
    node = None
    root_node = Node.objects.filter(slug=slugs[0]).first()

    if root_node is not None and root_node.typeOf.name in ROOT_NODE_TYPES:
        if len(slugs) > 1 and root_node.typeOf.name == 'service-group':
            child_node = root_node.children.filter(slug=slugs[1]).first()
            node = child_node if child_node is not None else root_node
        else:
            node = root_node

    return node


def fetch_dashboard(path):
    logger.info('fetch_dashboard: {}'.format(path))
    path_components = path.split('/')
    fetch_type = path_components[0]
    rest = path_components[1:]

    if fetch_type not in FETCH_TYPES:
        logger.warn('fetch_type "{}" is not valid'.format(fetch_type))
        return None

    if fetch_type == 'dashboard':
        logger.info('fetching dashboard for slug: {}'.format(rest[0]))
        logger.info(map(lambda d: d.slug, Dashboard.objects.all()))
        dashboard = Dashboard.objects.filter(slug=rest[0]).first()
        logger.info(dashboard)
    else:
        org_node = resolve_node(rest)

        if org_node is not None:
            dashboard = org_node.dashboard_set.filter(
                dashboard_type__in=TYPE_TO_TYPE[fetch_type]).first()
        else:
            dashboard = None

    return dashboard


@cache_control(max_age=60)
@csrf_exempt
@require_http_methods(['GET'])
@permission_required('dashboard')
def list_dashboards(user, request):
    parsed_dashboards = []

    for item in Dashboard.objects.all().order_by('title'):
        parsed_dashboards.append({
            'id': item.id,
            'title': item.title,
            'url': '{0}{1}'.format(
                settings.APP_ROOT,
                reverse('dashboard', kwargs={'identifier': item.slug})),
            'public-url': '{0}/performance/{1}'.format(
                settings.GOVUK_ROOT, item.slug),
            'published': item.published
        })

    return HttpResponse(to_json({'dashboards': parsed_dashboards}))


@csrf_exempt
@require_http_methods(['GET'])
@permission_required('dashboard')
def get_dashboard_by_slug(user, request, slug=None):
    dashboard = get_object_or_404(Dashboard, slug=slug)

    return HttpResponse(
        to_json(dashboard.serialize()),
        content_type='application/json'
    )


@csrf_exempt
@require_http_methods(['GET'])
@permission_required('dashboard')
def get_dashboard_by_uuid(user, request, dashboard_id=None):
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)

    return HttpResponse(
        to_json(dashboard.serialize()),
        content_type='application/json'
    )


@csrf_exempt
@require_http_methods(['POST', 'PUT', 'GET'])
@permission_required('dashboard')
@never_cache
@atomic_view
def dashboard(user, request, identifier=None):

    def add_module_and_children_to_dashboard(dashboard,
                                             module_data,
                                             parent=None):
        modules = []
        module = add_module_to_dashboard(dashboard, module_data, parent)
        modules.append(module)
        for module_data in module_data['modules']:
            modules.extend(add_module_and_children_to_dashboard(
                dashboard, module_data, module))
        return modules

    if request.method == 'GET':
        if is_uuid(identifier):
            return get_dashboard_by_uuid(request, identifier)
        else:
            return get_dashboard_by_slug(request, identifier)

    data = json.loads(request.body)

    # create a dashboard if we don't already have a dashboard slug
    if identifier is None and request.method == 'POST':
        dashboard = Dashboard()
    else:
        if is_uuid(identifier):
            dashboard = get_object_or_404(Dashboard, id=identifier)
        else:
            dashboard = get_object_or_404(Dashboard, slug=identifier)

    if data.get('organisation'):
        if not is_uuid(data['organisation']):
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
            organisation = Node.objects.get(id=data['organisation'])
            dashboard.organisation = organisation
        except Node.DoesNotExist:
            error = {
                'status': 'error',
                'message': 'Organisation does not exist',
                'errors': [create_error(request, 404,
                                        detail='Organisation does not exist')]
            }
            return HttpResponseBadRequest(to_json(error))

    for key, value in data.iteritems():
        if key not in ['organisation', 'links']:
            setattr(dashboard, key.replace('-', '_'), value)

    try:
        dashboard.full_clean()
    except ValidationError as error_details:
        errors = error_details.message_dict
        error_list = ['{0}: {1}'.format(field, ', '.join(errors[field]))
                      for field in errors]
        formatted_errors = ', '.join(error_list)
        error = {
            'status': 'error',
            'message': formatted_errors,
            'errors': [create_error(request, 400, title='validation error',
                                    detail=e)
                       for e in error_list]
        }
        return HttpResponseBadRequest(to_json(error))

    try:
        dashboard.save()
    except IntegrityError as e:
        error = {
            'status': 'error',
            'message': '{0}'.format(e.message),
            'errors': [create_error(request, 400, title='integrity error',
                                    detail=e.message)]
        }
        return HttpResponseBadRequest(to_json(error))

    if 'links' in data:
        for link_data in data['links']:
            if link_data['type'] == 'transaction':
                link, _ = dashboard.link_set.get_or_create(
                    link_type='transaction')
                link.url = link_data['url']
                link.title = link_data['title']
                link.save()
            else:
                dashboard.link_set.create(link_type=link_data.pop('type'),
                                          **link_data)

    if 'modules' in data:
        module_ids = set([m.id for m in dashboard.module_set.all()])

        for module_data in data['modules']:
            try:
                modules = add_module_and_children_to_dashboard(
                    dashboard, module_data)
                for m in modules:
                    module_ids.discard(m.id)
            except ValueError as e:
                error = {
                    'status': 'error',
                    'message': e.message,
                    'errors': [create_error(request, 400,
                                            detail=e.message)]
                }
                return HttpResponseBadRequest(to_json(error))

        Module.objects.filter(id__in=module_ids).delete()

    return HttpResponse(to_json(dashboard.serialize()),
                        content_type='application/json')

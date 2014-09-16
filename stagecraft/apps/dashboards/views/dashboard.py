import json
import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseNotFound)
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from stagecraft.apps.dashboards.models.dashboard import Dashboard
from stagecraft.apps.organisation.models import Node
from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.validation.validation import is_uuid
from stagecraft.libs.views.utils import to_json
from stagecraft.libs.views.transaction import atomic_view
from .module import add_module_to_dashboard

logger = logging.getLogger(__name__)


def dashboards_for_spotlight(request):
    dashboard_slug = request.GET.get('slug')
    dashboard = recursively_fetch_dashboard(dashboard_slug)
    if not dashboard:
        return error_response(dashboard_slug)
    dashboard_json = get_modules_or_tabs(dashboard_slug, dashboard)
    if not dashboard_json:
        return error_response(dashboard_slug)
    json_str = to_json(dashboard_json)

    response = HttpResponse(json_str, content_type='application/json')

    if dashboard.published:
        response['Cache-Control'] = 'max-age=300'
    else:
        response['Cache-Control'] = 'no-cache'

    return response


def error_response(dashboard_slug):
    error = {
        'status': 'error',
        'message': "No dashboard with slug '{}' exists".format(
            dashboard_slug)
    }
    logger.warn(error)
    return HttpResponseNotFound(to_json(error),
                                content_type='application/json')


def get_modules_or_tabs(request_slug, dashboard):
    # first part will always be empty as we never end the dashboard slug with
    # a slash
    dashboard_json = dashboard.spotlightify()
    remaining_parts = request_slug.replace(dashboard.slug, '').split('/')[1:]
    if len(remaining_parts) == 0:
        return dashboard_json
    if 'modules' not in dashboard_json:
        return None
    module = get_single_module_from_dashboard(
        remaining_parts[0], dashboard_json)
    if module is None:
        return None
    if len(remaining_parts) == 1:
        dashboard_json['modules'] = [module]
    elif len(remaining_parts) == 2:
        tab_slug = remaining_parts[1].replace(remaining_parts[0] + '-', '')
        tab = get_single_tab_from_module(tab_slug, module)
        if tab is None:
            return None
        tab['info'] = module['info']
        tab['title'] = module['title'] + ' - ' + tab['title']
        dashboard_json['modules'] = [tab]
    else:
        return None
    dashboard_json['page-type'] = 'module'
    return dashboard_json


def get_single_module_from_dashboard(module_slug, dashboard_json):
    return find_first_item_matching_slug(
        dashboard_json['modules'], module_slug)


def get_single_tab_from_module(tab_slug, module_json):
    return find_first_item_matching_slug(module_json['tabs'], tab_slug)


def find_first_item_matching_slug(item_list, slug):
    for item in item_list:
        if item['slug'] == slug:
            return item


def recursively_fetch_dashboard(dashboard_slug, count=3):
    if count == 0:
        return None

    dashboard = Dashboard.objects.filter(slug=dashboard_slug).first()

    if not dashboard:
        slug_parts = dashboard_slug.split('/')
        if len(slug_parts) > 1:
            slug_parts.pop()
            dashboard = recursively_fetch_dashboard(
                '/'.join(slug_parts), count=count - 1)

    return dashboard


@csrf_exempt
@require_http_methods(['GET'])
@permission_required('dashboard')
def get_dashboard(user, request, dashboard_id=None):
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
def dashboard(user, request, dashboard_id=None):

    if request.method == 'GET':
        return get_dashboard(request, dashboard_id)

    data = json.loads(request.body)

    # create a dashboard if we don't already have a dashboard ID
    if dashboard_id is None and request.method == 'POST':
        dashboard = Dashboard()
    else:
        dashboard = get_object_or_404(Dashboard, id=dashboard_id)

    if data.get('organisation'):
        if not is_uuid(data['organisation']):
            error = {
                'status': 'error',
                'message': 'Organisation must be a valid UUID',
            }
            return HttpResponseBadRequest(to_json(error))

        try:
            organisation = Node.objects.get(id=data['organisation'])
            dashboard.organisation = organisation
        except Node.DoesNotExist:
            error = {
                'status': 'error',
                'message': 'Organisation does not exist',
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
        }
        return HttpResponseBadRequest(to_json(error))

    try:
        dashboard.save()
    except IntegrityError as e:
        error = {
            'status': 'error',
            'message': '{0}'.format(e.message),
        }
        return HttpResponseBadRequest(to_json(error))

    if 'links' in data:
        for link_data in data['links']:
            dashboard.link_set.create(link_type=link_data.pop('type'),
                                      **link_data)

    if 'modules' in data:
        for i, module_data in enumerate(data['modules'], start=1):
            if 'id' in module_data:
                raise NotImplemented("Not yet implemented updates")
            else:
                try:
                    add_module_to_dashboard(dashboard, module_data)
                except ValueError as e:
                    error = {
                        'status': 'error',
                        'message': 'Failed to create module {}: {}'.format(
                            i, e.message),
                    }
                    return HttpResponse(to_json(error), status=400)

    return HttpResponse(to_json(dashboard.serialize()),
                        content_type='application/json')

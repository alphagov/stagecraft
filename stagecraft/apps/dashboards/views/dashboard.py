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


# Spotlight stuff
def dashboards_for_spotlight(request):
    dashboard_slug = request.GET.get('slug')
    if not dashboard_slug:
        return dashboard_list_for_spotlight()
    else:
        return single_dashboard_for_spotlight(dashboard_slug)


def dashboard_list_for_spotlight():
    dashboard_json = Dashboard.list_for_spotlight()
    json_str = to_json(dashboard_json)
    response = HttpResponse(json_str, content_type='application/json')
    response['Cache-Control'] = 'max-age=300'
    return response


def single_dashboard_for_spotlight(dashboard_slug):
    dashboard = recursively_fetch_dashboard(dashboard_slug)
    if not dashboard:
        return error_response(dashboard_slug)
    dashboard_json = dashboard.spotlightify(dashboard_slug)
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


# Admin app stuff
@csrf_exempt
@require_http_methods(['GET'])
@permission_required('dashboard')
def list_dashboards(user, request):
    parsed_dashboards = []

    for item in Dashboard.objects.all():
        parsed_dashboards.append({
            'id': item.id,
            'title': item.title,
            'url': '{0}{1}'.format(
                settings.APP_ROOT,
                reverse('dashboard', kwargs={'dashboard_id': item.id})),
            'public-url': '{0}/performance/{1}'.format(
                settings.GOVUK_ROOT, item.slug),
            'published': item.published
        })

    return HttpResponse(to_json({'dashboards': parsed_dashboards}))


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
@require_http_methods(['PUT'])
@permission_required('dashboard')
@never_cache
@atomic_view
def update_dashboard(user, request, dashboard_id=None):
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)
    return update_or_setup_dashboard_and_respond(request, dashboard)


@csrf_exempt
@require_http_methods(['POST'])
@permission_required('dashboard')
@never_cache
@atomic_view
def create_dashboard(user, request):
    dashboard = Dashboard()
    return update_or_setup_dashboard_and_respond(request, dashboard)


@csrf_exempt
@require_http_methods(['POST', 'PUT', 'GET'])
@permission_required('dashboard')
@never_cache
@atomic_view
def dashboard(user, request, dashboard_id=None):
    if request.method == 'GET':
        return get_dashboard(request, dashboard_id)
    if request.method == 'POST':
        return create_dashboard(request)
    if request.method == 'PUT':
        return update_dashboard(request, dashboard_id)


def update_or_setup_dashboard_and_respond(request, dashboard):
    dashboard, response = set_dashboard_fields_or_error_response(
        request, dashboard)
    if response:
        return response
    dashboard, response = validate_dashboard_or_error_response(dashboard)
    if response:
        return response
    dashboard, response = save_dashboard_or_error_response(dashboard)
    if response:
        return response
    dashboard = add_dashboard_links(request, dashboard)
    dashboard, response = set_dashboard_modules_or_error_response(
        request, dashboard)
    if response:
        return response
    return HttpResponse(to_json(dashboard.serialize()),
                        content_type='application/json')


def set_dashboard_fields_or_error_response(request, dashboard):
    data = json.loads(request.body)

    if data.get('organisation'):
        if not is_uuid(data['organisation']):
            error = {
                'status': 'error',
                'message': 'Organisation must be a valid UUID',
            }
            return dashboard, HttpResponseBadRequest(to_json(error))

        try:
            organisation = Node.objects.get(id=data['organisation'])
            dashboard.organisation = organisation
        except Node.DoesNotExist:
            error = {
                'status': 'error',
                'message': 'Organisation does not exist',
            }
            return dashboard, HttpResponseBadRequest(to_json(error))

    for key, value in data.iteritems():
        if key not in ['organisation', 'links']:
            setattr(dashboard, key.replace('-', '_'), value)
    return dashboard, None


def validate_dashboard_or_error_response(dashboard):
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
        return dashboard, HttpResponseBadRequest(to_json(error))
    return dashboard, None


def save_dashboard_or_error_response(dashboard):
    try:
        dashboard.save()
    except IntegrityError as e:
        error = {
            'status': 'error',
            'message': '{0}'.format(e.message),
        }
        return dashboard, HttpResponseBadRequest(to_json(error))
    return dashboard, None


def add_dashboard_links(request, dashboard):
    data = json.loads(request.body)
    if 'links' in data:
        for link_data in data['links']:
            dashboard.link_set.create(link_type=link_data.pop('type'),
                                      **link_data)
    return dashboard


def set_dashboard_modules_or_error_response(request, dashboard):
    data = json.loads(request.body)
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
                    return dashboard, HttpResponse(to_json(error), status=400)
    return dashboard, None

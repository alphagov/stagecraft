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
from ..models.module import Module

logger = logging.getLogger(__name__)


def create_error(request, status, code='', title='', detail=''):
    """creates a JSON API error - http://jsonapi.org/format/#errors

    "status" - The HTTP status code applicable to this problem,
               expressed as a string value.
    "code" - An application-specific error code, expressed as a
             string value.
    "title" - A short, human-readable summary of the problem. It
              SHOULD NOT change from occurrence to occurrence of
              the problem, except for purposes of localization.
    "detail" - A human-readable explanation specific to this
               occurrence of the problem.
    """
    return {
        'id': request.META.get('HTTP_REQUEST_ID', ''),
        'status': str(status),
        'code': code,
        'title': title,
        'detail': detail,
    }


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
    dashboard = recursively_fetch_dashboard(dashboard_slug)
    if not dashboard:
        return error_response(request, dashboard_slug)
    dashboard_json = dashboard.spotlightify(dashboard_slug)
    if not dashboard_json:
        return error_response(request, dashboard_slug)
    json_str = to_json(dashboard_json)

    response = HttpResponse(json_str, content_type='application/json')

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
def list_dashboards(user, request):
    parsed_dashboards = []

    for item in Dashboard.objects.all():
        parsed_dashboards.append({
            'id': item.id,
            'title': item.title,
            'url': '{0}{1}'.format(
                settings.APP_ROOT,
                reverse('dashboard', kwargs={'slug': item.slug})),
            'public-url': '{0}/performance/{1}'.format(
                settings.GOVUK_ROOT, item.slug),
            'published': item.published
        })

    return HttpResponse(to_json({'dashboards': parsed_dashboards}))


@csrf_exempt
@require_http_methods(['GET'])
@permission_required('dashboard')
def get_dashboard(user, request, slug=None):
    dashboard = get_object_or_404(Dashboard, slug=slug)

    return HttpResponse(
        to_json(dashboard.serialize()),
        content_type='application/json'
    )


@csrf_exempt
@require_http_methods(['POST', 'PUT', 'GET'])
@permission_required('dashboard')
@never_cache
@atomic_view
def dashboard(user, request, slug=None):

    if request.method == 'GET':
        return get_dashboard(request, slug)

    data = json.loads(request.body)

    # create a dashboard if we don't already have a dashboard slug
    if slug is None and request.method == 'POST':
        dashboard = Dashboard()
    else:
        dashboard = get_object_or_404(Dashboard, slug=slug)

    if data.get('organisation'):
        if not is_uuid(data['organisation']):
            error = {
                'status': 'error',
                'message': 'Organisation must be a valid UUID',
                'errors': [create_error(request, 400,
                           detail='Organisation must be a valid UUID')],
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
        for i, module_data in enumerate(data['modules'], start=1):
            try:
                add_module_to_dashboard(dashboard, module_data)
            except ValueError as e:
                error = {
                    'status': 'error',
                    'message': 'Failed to create module {}: {}'.format(
                        i, e.message),
                    'errors': [create_error(request, 400,
                                            detail=e.message)]
                }
                return HttpResponse(to_json(error), status=400)

    return HttpResponse(to_json(dashboard.serialize()),
                        content_type='application/json')

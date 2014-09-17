import json
import logging

from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
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
from stagecraft.libs.views.utils import to_json
from .module import add_module_to_dashboard

logger = logging.getLogger(__name__)


def dashboards_for_spotlight(request):
    dashboard_slug = request.GET.get('slug')
    dashboard = recursively_fetch_dashboard(dashboard_slug)
    if not dashboard:
        error = {
            'status': 'error',
            'message': "No dashboard with slug '{}' exists".format(
                dashboard_slug)
        }
        logger.warn(error)
        return HttpResponseNotFound(to_json(error))
    json_str = to_json(dashboard.spotlightify())

    response = HttpResponse(json_str, content_type='application/json')

    if dashboard.published:
        response['Cache-Control'] = 'max-age=300'
    else:
        response['Cache-Control'] = 'no-cache'

    return response


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
        with transaction.atomic():
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
        for module_data in data['modules']:
            if 'id' in module_data:
                raise NotImplemented("Not yet implemented updates")
            else:
                add_module_to_dashboard(dashboard, module_data)

    return HttpResponse(to_json(dashboard.serialize()),
                        content_type='application/json')

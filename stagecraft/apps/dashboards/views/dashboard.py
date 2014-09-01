import json
import logging

from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.csrf import csrf_exempt

from stagecraft.apps.dashboards.models.dashboard import Dashboard
from stagecraft.apps.organisation.models import Node
from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.views.utils import to_json

# this needs to go somewhere EVEN MORE COMMON

logger = logging.getLogger(__name__)


def dashboards(request):
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
                '/'.join(slug_parts), count=count-1)

    return dashboard


@csrf_exempt
@permission_required('dashboard')
@never_cache
def dashboard(user, request):
    data = json.loads(request.body)

    organisation = Node.objects.get(id=data['organisation'])
    dashboard = Dashboard()
    dashboard.organisation = organisation
    for key, value in data.iteritems():
        if key != 'organisation':
            setattr(dashboard, key.replace('-', '_'), value)

    dashboard.save()

    return HttpResponse(json.dumps({'status': 'ok'}),
                        content_type='application/json')

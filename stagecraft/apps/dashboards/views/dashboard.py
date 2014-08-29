import logging
from django.http import HttpResponse, HttpResponseNotFound
from stagecraft.libs.views.utils import to_json
from stagecraft.apps.dashboards.models.dashboard import Dashboard

# this needs to go somewhere EVEN MORE COMMON

logger = logging.getLogger(__name__)


def dashboards(request):
    dashboard_slug = request.GET.get('slug')
    dashboard = Dashboard.objects.filter(slug=dashboard_slug).first()
    if not dashboard:
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

    return HttpResponse(json_str, content_type='application/json')


def recursively_fetch_dashboard(dashboard_slug, count=3):
    if count == 0:
        return None
    slug_parts = dashboard_slug.split('/')
    current_part = slug_parts.pop()
    dashboard = Dashboard.objects.filter(slug=current_part).first()
    if not dashboard:
        if slug_parts:
            count -= 1
            dashboard = recursively_fetch_dashboard(
                ('/').join(slug_parts), count=count)
        else:
            return None
    return dashboard

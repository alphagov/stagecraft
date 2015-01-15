import json

from stagecraft.libs.views.utils import to_json

from django.http import HttpResponse
from django.db import connection
from ..models import Dashboard


def dashboards_by_tx(request, identifier):
    dashboards = Dashboard.objects.by_tx_id(identifier)

    serialized_dashboards = \
        [dashboard.serialize() for dashboard in dashboards]

    return HttpResponse(
        to_json(serialized_dashboards),
        content_type='application/json',
        status=200
    )

import json

from django.http import HttpResponse
from django.views.decorators.cache import never_cache


@never_cache
def status(request):
    return HttpResponse(
        json.dumps({'status': 'ok'}),
        content_type='application/json')

from stagecraft.apps.datasets.views.common.utils import *
import logging

from django.conf import settings
from django.http import (HttpResponse, HttpResponseNotFound)
from django.views.decorators.vary import vary_on_headers

from stagecraft.apps.datasets.models import BackdropUser

logger = logging.getLogger(__name__)


@permission_required('user')
@long_cache
@vary_on_headers('Authorization')
def detail(user, request, email):
    try:
        backdrop_user = BackdropUser.objects.get(email=email)
    except BackdropUser.DoesNotExist:
        error = {
            'status': 'error',
            'message': "No user with email address '{}' exists".format(email)
        }
        logger.warn(error)
        return HttpResponseNotFound(to_json(error))

    json_str = to_json(backdrop_user.serialize())

    return HttpResponse(json_str, content_type='application/json')

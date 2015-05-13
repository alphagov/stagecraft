import logging

from django.http import (HttpResponse, HttpResponseNotFound)
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers

from stagecraft.apps.users.models import User
from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.views.utils import to_json, create_error

logger = logging.getLogger(__name__)


@permission_required('user')
@never_cache
@vary_on_headers('Authorization')
def detail(authorised_user, request, email):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        error = {
            'status': 'error',
            'message': "No user with email address '{}' exists".format(email)
        }
        logger.warn(error)

        error["errors"] = [
            create_error(request, 404, detail=error['message'])
        ]

        return HttpResponseNotFound(to_json(error))

    json_str = to_json(user.serialize())

    return HttpResponse(json_str, content_type='application/json')

import logging
import json
import requests

from stagecraft.apps.datasets.models import OAuthUser
from stagecraft.libs.validation.validation import extract_bearer_token
from stagecraft.libs.views.utils import create_error
from django.conf import settings
from django.http import (HttpResponseForbidden, HttpResponse, HttpRequest)
from django_statsd.clients import statsd

audit_logger = logging.getLogger('stagecraft.audit')


@statsd.timer('get_user.both')
def _get_user(access_token, anon_allowed):
    user = None
    if access_token is not None:

        if settings.USE_DEVELOPMENT_USERS is True:
            try:
                user = settings.DEVELOPMENT_USERS[access_token]
            except KeyError:
                user = None
        else:
            user = _get_user_from_database(access_token)
            if user is None:
                user = _get_user_from_signon(access_token)
                if user is not None:
                    _set_user_to_database(access_token, user)
    elif anon_allowed:
        user = {
            "email": "performance@digital.cabinet-office.gov.uk",
            "name": "Anonymous",
            "organisation_slug": "cabinet-office",
            "permissions": [
            ],
            "uid": "00000000-0000-0000-0000-000000000000"
        }

    return user


@statsd.timer('get_user.signon')
def _get_user_from_signon(access_token):
    response = requests.get(
        '{0}/user.json?client_id={1}'.format(
            settings.SIGNON_URL, settings.SIGNON_CLIENT_ID),
        headers={'Authorization': 'Bearer {0}'.format(access_token)}
    )
    if response.status_code == 200:
        return response.json()['user']


@statsd.timer('get_user.postgres')
def _get_user_from_database(access_token):
    oauth_user = OAuthUser.objects.get_by_access_token(access_token)
    if oauth_user:
        return oauth_user.serialize()


def _set_user_to_database(access_token, user):
    OAuthUser.objects.cache_user(access_token, user)


def check_permission(access_token, permission_requested, anon_allowed=True):
    user = _get_user(access_token, anon_allowed)
    has_permission = user is not None and \
        (permission_requested is None or
         permission_requested in user['permissions'])
    return (user, has_permission)


def unauthorized(request, message):
    doc = {
        'status': 'error',
        'message': 'Unauthorized: {}'.format(message),
    }
    doc["errors"] = [create_error(request, 401, detail=doc["message"])]
    response = HttpResponse(to_json(doc), status=401)
    response['WWW-Authenticate'] = 'Bearer'
    return response


def forbidden(request, message):
    doc = {
        'status': 'error',
        'message': 'Forbidden: {}'.format(message),
    }
    doc["errors"] = [create_error(request, 403, detail=doc["message"])]
    return HttpResponseForbidden(to_json(doc))


def authorize(request, permission, anon_allowed=True):
    access_token = extract_bearer_token(request)
    (user, has_permission) = check_permission(
        access_token, permission, anon_allowed
    )

    if user is None:
        return user, unauthorized(request, 'invalid access token.')
    elif not has_permission:
        return user, forbidden(request, 'user lacks permission.')
    else:
        extra = {
            'token': access_token,
        }
        if request.method in ['POST', 'PUT']:
            extra['body'] = request.body
        audit_logger.info('Authorised action', extra=extra)
        return user, None


def permission_required(permission=None):
    def decorator(a_view):
        def _wrapped_view(request, *args, **kwargs):
            user, err = authorize(request, permission, anon_allowed=False)

            if err:
                return err
            else:
                return a_view(user, request, *args, **kwargs)
        return _wrapped_view
    return decorator


def to_json(what):
    return json.dumps(what, indent=1)

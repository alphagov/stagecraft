import json
import requests
from stagecraft.apps.datasets.models import OAuthUser
from stagecraft.libs.validation.validation import extract_bearer_token
from django.conf import settings
from django.http import (HttpResponseForbidden)
from django.utils.cache import patch_response_headers
from statsd.defaults.django import statsd
from functools import wraps


@statsd.timer('get_user.timer')
def _get_user(access_token):
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

    return user


def _get_user_from_signon(access_token):
    response = requests.get(
        '{0}/user.json'.format(settings.SIGNON_URL),
        headers={'Authorization': 'Bearer {0}'.format(access_token)}
    )
    if response.status_code == 200:
        return response.json()['user']


def _get_user_from_database(access_token):
    try:
        oauth_user = OAuthUser.objects.get(access_token=access_token)
        # check expiry
        return {
            "uid": oauth_user.uid,
            "email": oauth_user.email,
            "permissions": oauth_user.permissions,
        }
    except OAuthUser.DoesNotExist:
        pass
    return None


def _set_user_to_database(access_token, user):
    pass


def check_permission(access_token, permission_requested):
    user = _get_user(access_token)
    has_permission = user is not None and \
        permission_requested in user['permissions']
    return (user, has_permission)


def permission_required(permission):
    def decorator(a_view):
        def _wrapped_view(request, *args, **kwargs):

            access_token = extract_bearer_token(request)
            (user, has_permission) = check_permission(access_token, permission)

            if user is None:
                return HttpResponseForbidden(to_json({
                    'status': 'error',
                    'message': 'Forbidden: invalid or no token given.'
                }))
            elif not has_permission:
                return HttpResponseForbidden(to_json({
                    'status': 'error',
                    'message': 'Forbidden: user lacks permission.'
                }))
            else:
                return a_view(user, request, *args, **kwargs)
        return _wrapped_view
    return decorator


def long_cache(a_view):
    @wraps(a_view)
    def _wrapped_view(request, *args, **kwargs):
        response = a_view(request, *args, **kwargs)
        patch_response_headers(response, 86400 * 365)
        return response
    return _wrapped_view


def to_json(what):
    return json.dumps(what, indent=1)

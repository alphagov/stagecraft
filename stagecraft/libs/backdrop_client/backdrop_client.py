from __future__ import unicode_literals

from functools import wraps
import json
import logging
import requests

from contextlib import contextmanager

from django.conf import settings

logger = logging.getLogger(__name__)

_DISABLED = False


class BackdropError(Exception):
    pass


class BackdropUnknownError(BackdropError):

    def __str__(self):
        return 'Unknown Backdrop error: {}'.format(
            super(BackdropUnknownError, self).__str__())


class BackdropConnectionError(BackdropError):

    def __str__(self):
        return 'Error connecting to Backdrop: {}'.format(
            super(BackdropConnectionError, self).__str__())


class BackdropAuthenticationError(BackdropError):

    def __str__(self):
        return 'Error authenticating with Backdrop: {}'.format(
            super(BackdropAuthenticationError, self).__str__())


class BackdropBadRequestError(BackdropError):

    def __str__(self):
        return 'Bad request to Backdrop: {}'.format(
            super(BackdropBadRequestError, self).__str__())


class BackdropNotFoundError(BackdropError):

    def __str__(self):
        return 'Not found in Backdrop: {}'.format(
            super(BackdropNotFoundError, self).__str__())


@contextmanager
def backdrop_connection_disabled():
    """
    Context manager to temporarily disable any connection out to Backdrop.
    WARNING: This is not thread-safe.
    """
    global _DISABLED
    _DISABLED = True
    try:
        yield
    finally:
        _DISABLED = False


def check_disabled(func):
    """
    Decorator to wrap up checking if the Backdrop
    connection is set to disabled or not
    """
    @wraps(func)
    def _check(*args, **kwargs):
        if _DISABLED:
            return
        else:
            return func(*args, **kwargs)
    return _check


def disable_backdrop_connection(func):
    """
    Decorator to temporarily disable any connection out to Backdrop.
    WARNING: This is not thread-safe.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with backdrop_connection_disabled():
            return func(*args, **kwargs)
    return wrapper


def _get_headers():
    auth_value = 'Bearer ' + settings.STAGECRAFT_COLLECTION_ENDPOINT_TOKEN
    return {
        'Authorization': auth_value,
        'content-type': 'application/json'
    }


@check_disabled
def delete_data_set(name):
    """
    Connect to Backdrop and delete a collection called ``name``.
    """

    endpoint_url = '{url}/data-sets/{name}'.format(url=settings.BACKDROP_URL,
                                                   name=name)

    backdrop_request = lambda: requests.delete(
        endpoint_url,
        headers=_get_headers())

    _send_backdrop_request(backdrop_request)


def _send_backdrop_request(backdrop_request):
    try:
        response = backdrop_request()
    except requests.exceptions.ConnectionError as e:
        raise BackdropConnectionError(e)

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.exception(e)
        logger.error(response.content)

        error_message = _get_backdrop_error_message(response)

        if response.status_code == 400:
            raise BackdropBadRequestError(error_message)

        elif response.status_code == 404:
            raise BackdropNotFoundError(error_message)

        elif response.status_code in (401, 403):
            raise BackdropAuthenticationError(error_message)

        else:
            raise BackdropUnknownError("{}\n{}".format(repr(e), error_message))


def _get_backdrop_error_message(response):
    """
    Backdrop should return an error as response with a JSON body like
    {'status': 'error', 'message': 'Some error message'}
    This attempts to extract the 'Some error message' string. If that fails,
    return the raw JSON string.
    """
    try:
        return response.json()['message']
    except Exception:
        return response.content

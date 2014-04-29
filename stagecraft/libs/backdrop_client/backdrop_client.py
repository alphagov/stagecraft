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


def create_data_set(name, capped_size):
    """
    Connect to Backdrop and create a new collection called ``name``.
    Specify ``capped_size`` in bytes to create a capped collection, or 0 to
    create an uncapped collection.
    """
    if _DISABLED:
        return

    if not isinstance(capped_size, int) or capped_size < 0:
        raise BackdropError(
            "capped_size must be 0 or a positive integer number of bytes.")

    json_request = json.dumps({'capped_size': capped_size})

    endpoint_url = '{url}/data-sets/{name}'.format(url=settings.BACKDROP_URL,
                                                   name=name)

    response = requests.post(endpoint_url,
                             headers=_get_headers(),
                             data=json_request)

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.exception(e)
        logger.error(response.content)
        raise BackdropError("{}\n{}".format(repr(e), response.content))


def delete_data_set(name):
    """
    Connect to Backdrop and delete a collection called ``name``.
    """
    if _DISABLED:
        return

    endpoint_url = '{url}/data-sets/{name}'.format(url=settings.BACKDROP_URL,
                                                   name=name)

    response = requests.delete(endpoint_url, headers=_get_headers())

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.exception(e)
        logger.error(response.content)
        raise BackdropError("{}\n{}".format(repr(e), response.content))

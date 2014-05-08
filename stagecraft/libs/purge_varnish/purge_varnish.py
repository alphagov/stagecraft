from __future__ import unicode_literals

from functools import wraps
from contextlib import contextmanager

import requests

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_DISABLED = False


@contextmanager
def purge_varnish_disabled():
    """
    Context manager to temporarily disable any PURGE requests being sent to
    Varnish.
    WARNING: This is not thread-safe.
    """
    global _DISABLED
    _DISABLED = True
    try:
        yield
    finally:
        _DISABLED = False


def disable_purge_varnish(func):
    """
    Decorator to temporarily disable any PURGE requests being sent to Varnish.
    WARNING: This is not thread-safe.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with purge_varnish_disabled():
            return func(*args, **kwargs)
    return wrapper


def purge(path_queries, varnish_caches=None):
    """
    @path_queries -> ['/data-sets', '/data-sets/govuk_visitors']

    Construct full URLs from the path queries and purge them from the varnish
    caches.
    """
    if _DISABLED:
        return

    if not varnish_caches:
        varnish_caches = get_varnish_caches()

    app_hostname = getattr(settings, 'APP_HOSTNAME', None)
    if not app_hostname:
        raise ImproperlyConfigured("Couldn't get APP_HOSTNAME from settings")

    for url_to_purge in get_varnish_purge_urls_for_path_queries(
            path_queries, varnish_caches):
        # url_to_purge  eg frontend-app-1.whatever.com/data-sets
        # app_hostname eg stagecraft.preview.performance.service.gov.uk
        send_purge(url_to_purge, app_hostname)


def get_varnish_purge_urls_for_path_queries(
        path_queries, varnish_caches=None):
    """
    in: ['/data-sets']
    out:
    - frontend-1-blah/data-sets
    - frontend-2-blah/data-sets

    """
    if not varnish_caches:
        varnish_caches = get_varnish_caches()

    for varnish_host, varnish_port in varnish_caches:
        for path_query in path_queries:
            purge_url = '{}:{}{}'.format(
                varnish_host, varnish_port, path_query)
            yield purge_url


def send_purge(varnish_url, app_hostname):
    headers = {'Host': app_hostname}
    response = requests.request('PURGE', varnish_url, headers=headers)
    response.raise_for_status()


def get_varnish_caches():
    """
    Return an iterable of tuples of the form:
    ('https://varnish-1.somewhere.com', 7999)
    """
    host_and_ports = getattr(settings, 'VARNISH_CACHES', None)

    if not host_and_ports:
        raise ImproperlyConfigured("Missing VARNISH_CACHES setting.")

    return host_and_ports

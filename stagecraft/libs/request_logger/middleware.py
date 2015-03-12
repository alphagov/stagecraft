# encoding: utf-8

from __future__ import unicode_literals

import logging
import time

from threading import local


logger = logging.getLogger(__name__)

_thread_locals = local()


def get_current_request():
    """ returns the request object for this thead """
    return getattr(_thread_locals, "request", None)


class RequestLoggerMiddleware(object):

    def process_request(self, request):
        _thread_locals.request = request
        request.start_request_time = time.time()
        logger.info("{method} {path}".format(
            method=request.method,
            path=request.get_full_path()),
            extra={
                'request_method': request.method,
                'http_host': request.META.get('HTTP_HOST'),
                'http_path': request.get_full_path(),
                'request_id': request.META.get('HTTP_REQUEST_ID')
        })

    def process_response(self, request, response):
        if hasattr(request, 'start_request_time'):
            elapsed_time = time.time() - request.start_request_time
            logger.info("{method} {path} : {status} {secs:.6f}s".format(
                method=request.method,
                path=request.get_full_path(),
                status=response.status_code,
                secs=elapsed_time),
                extra={
                    'request_method': request.method,
                    'http_host': request.META.get('HTTP_HOST'),
                    'http_path': request.get_full_path(),
                    'status': response.status_code,
                    'request_time': elapsed_time,
            })
        return response


class AdditionalFieldsFilter(logging.Filter):

    def filter(self, record):
        request = get_current_request()
        if request:
            record.request_method = request.method,
            record.http_host = request.META.get('HTTP_HOST'),
            record.http_path = request.get_full_path(),
            record.request_id = request.META.get('HTTP_REQUEST_ID')
        return 1

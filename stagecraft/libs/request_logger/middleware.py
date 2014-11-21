# encoding: utf-8

from __future__ import unicode_literals

import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(object):
    def process_request(self, request):
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

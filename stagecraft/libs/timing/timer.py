import time
import logging

logger = logging.getLogger(__name__)


def timeit(method, capture_query=False):

    def timed(*args, **kw):
        ts = time.time()
        query_info = {}
        if capture_query:
            query_info = {'query': args[1]}
        logger.info('{!r} starting'.format(method.__name__), extra=query_info)
        result = method(*args, **kw)
        te = time.time()
        elapsed = te - ts
        extra = {
            'elapsed_time': elapsed, 'method_args': args, 'kw': kw
        }
        extra.update(query_info)
        logger.info(
            '{!r} took {:.2f}'.format(
                method.__name__, elapsed),
            extra=extra)
        return result

    return timed

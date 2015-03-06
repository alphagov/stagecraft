import time
import logging

logger = logging.getLogger(__name__)


def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        logger.info('{!r} starting'.format(method.__name__))
        result = method(*args, **kw)
        te = time.time()
        elapsed = te - ts
        logger.info(
            '{!r} took {:.2f}'.format(
                method.__name__, elapsed),
            extra={'elapsed_time': elapsed, 'method_args': args, 'kw': kw})
        return result

    return timed

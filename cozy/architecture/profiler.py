import time
import logging
import functools

log = logging.getLogger("timing")

def timing(f):
    @functools.wraps(f)
    def wrap(*args):
        time1 = time.perf_counter()
        ret = f(*args)
        time2 = time.perf_counter()
        log.info('{:s} function took {:.3f} ms'.format(f.__name__, (time2-time1)*1000.0))

        return ret
    return wrap
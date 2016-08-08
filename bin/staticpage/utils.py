# -*- coding: utf-8 -*-

import errno
import logging
import os


# http://stackoverflow.com/a/600612/596531
def mkdirp(path):
    """``mkdir -p`` for Python."""
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def init_logger():
    log = logging.getLogger('webassets')
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)

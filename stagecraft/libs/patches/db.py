import django
from django.db.backends import util

from django_statsd.patches.utils import wrap, patch_method
from django_statsd.clients import statsd

import logging

from stagecraft.libs.timing.timer import timeit

logger = logging.getLogger(__name__)


def key(db, attr):
    return 'db.%s.%s.%s' % (db.client.executable_name, db.alias, attr)


def pre_django_1_6_cursorwrapper_getattr(self, attr):
    """
    The CursorWrapper is a pretty small wrapper around the cursor.
    If you are NOT in debug mode, this is the wrapper that's used.
    Sadly if it's in debug mode, we get a different wrapper.
    """
    if self.db.is_managed():
        self.db.set_dirty()
    if attr in self.__dict__:
        return self.__dict__[attr]
    else:
        if attr in ['execute', 'executemany', 'callproc']:
            return wrap(getattr(self.cursor, attr), key(self.db, attr))
        return getattr(self.cursor, attr)


def _get_query_type(query):
    return (query.split(None, 1) or ['__empty__'])[0].lower()


def patched_execute(orig_execute, self, query, *args, **kwargs):
    timed_execute = timeit(orig_execute, capture_query=True)
    return timed_execute(self, query, *args, **kwargs)


def patched_executemany(orig_executemany, self, query, *args, **kwargs):
    timed_executemany = timeit(orig_executemany, capture_query=True)
    return timed_executemany(self, query, *args, **kwargs)


def patched_callproc(orig_callproc, self, query, *args, **kwargs):
    timed_callproc = timeit(orig_callproc, capture_query=True)
    return timed_callproc(self, query, *args, **kwargs)


def patch():
    """
    The CursorWrapper is a pretty small wrapper around the cursor.  If
    you are NOT in debug mode, this is the wrapper that's used.  Sadly
    if it's in debug mode, we get a different wrapper for version
    earlier than 1.6.
    """

    # In 1.6+ util.CursorDebugWrapper just makes calls to CursorWrapper
    # As such, we only need to instrument CursorWrapper.
    # Instrumenting both will result in duplicated metrics
    patch_method(util.CursorWrapper, 'execute')(patched_execute)
    patch_method(util.CursorWrapper, 'executemany')(patched_executemany)
    patch_method(util.CursorWrapper, 'callproc')(patched_callproc)
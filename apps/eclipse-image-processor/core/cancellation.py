"""Cooperative cancellation isolated to one preview job and its helper threads."""
from contextlib import contextmanager
from contextvars import ContextVar

_active_event = ContextVar('preview_cancellation_event', default=None)


class ProcessingCancelled(Exception):
    """Normal termination of an obsolete preview, not a filter failure."""


def cancellation_check():
    """Capture the job token so nested thread pools can check the same request."""
    event = _active_event.get()
    def check():
        if event is not None and event.is_set():
            raise ProcessingCancelled()
    return check


def check_cancelled():
    event = _active_event.get()
    if event is not None and event.is_set():
        raise ProcessingCancelled()


@contextmanager
def cancellation_scope(event):
    token = _active_event.set(event)
    try:
        check_cancelled()
        yield
        check_cancelled()
    finally:
        _active_event.reset(token)

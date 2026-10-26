"""Let queued GUI task completions run before inspecting the displayed result."""
import time
from PySide6.QtTest import QTest


def wait_for_gui(window, timeout=10000):
    deadline = time.monotonic() + timeout/1000
    while (getattr(window, '_load_thread', None) is not None or
           getattr(window, '_geometry_thread', None) is not None or
           getattr(getattr(window,'background',None),'thread',None) is not None or
           getattr(window, '_presentation_thread', None) is not None or
           getattr(window, '_presentation_request', None) is not None):
        if time.monotonic() > deadline:
            raise AssertionError('GUI background task did not finish')
        QTest.qWait(10)


def close_window(window):
    window.close()
    if hasattr(window, 'persistent_thread'):
        wait_for_gui(window)
        deadline = time.monotonic() + 10
        while window.persistent_thread.isRunning() or getattr(window, '_export_thread', None) is not None:
            if time.monotonic() > deadline:
                raise AssertionError('Window did not finish closing')
            QTest.qWait(10)
        QTest.qWait(1)

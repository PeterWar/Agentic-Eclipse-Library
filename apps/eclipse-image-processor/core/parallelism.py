"""One CPU budget per independent filter, inherited by nested helper tasks."""
from contextlib import contextmanager
from contextvars import ContextVar
import os

CPU_CORES = os.cpu_count() or 4
_filter_budget = ContextVar('filter_cpu_budget', default=CPU_CORES)


def filter_cpu_budget():
    return _filter_budget.get()


@contextmanager
def filter_budget(workers):
    token=_filter_budget.set(max(1,int(workers)))
    try:
        yield
    finally:
        _filter_budget.reset(token)


def layer_workers(source, count):
    """Bound scratch memory as well as CPU; conservative unknown-memory fallback.

    128 bytes/pixel/filter estimates scratch space, not measured peak RSS.
    Reserve two thirds of physical RAM for caches, GUI, OS and other applications.
    """
    try:
        memory=os.sysconf('SC_PHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')//3
    except (AttributeError,ValueError,OSError):
        memory=512*1024**2
    # shortcut: scratch estimates are per pixel; measure per-operator peaks if larger masters exceed the budget.
    memory_limit=max(1,memory//max(1,source.size*128))
    size_limit=2 if source.size>4_000_000 else 4
    return max(1,min(count,CPU_CORES,size_limit,memory_limit))

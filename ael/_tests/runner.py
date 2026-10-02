"""Dependency-light runner. Skips are reported as not checked."""
import importlib
import time
import traceback
import unittest


def run(name_filter=''):
    cases=[]
    for module in ('test_ael','test_develop'):
        m=importlib.import_module(f'ael._tests.{module}')
        cases.extend((n,getattr(m,n)) for n in dir(m) if n.startswith('test_') and name_filter in n)
    if not cases:
        print(f'no test matches {name_filter!r}: nothing was checked')
        return 1
    failed=skipped=0
    for name,fn in sorted(cases):
        t=time.monotonic()
        try:
            fn(); print(f'PASS  {name}  ({time.monotonic()-t:.1f} s)',flush=True)
        except unittest.SkipTest as e:
            skipped+=1; print(f'SKIP  {name}: {e} (not checked)',flush=True)
        except Exception:
            failed+=1; print(f'FAIL  {name}',flush=True); traceback.print_exc()
    checked=len(cases)-skipped
    print(f'{checked-failed}/{checked} passed; {skipped} skipped (not checked)',flush=True)
    return int(failed>0 or checked==0)

"""Run the tests without pytest: ``python tests/run_tests.py [name_filter]``."""
import sys
import time
import traceback
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # also under `python -m ael selftest`
import test_ael  # noqa: E402

flt = sys.argv[1] if len(sys.argv) > 1 else ""
names = [n for n in dir(test_ael) if n.startswith("test_") and flt in n]
if not names:
    print(f"no test matches {flt!r}: nothing was checked")
    sys.exit(1)
fails = skipped = 0
for n in names:
    t0 = time.time()
    try:
        getattr(test_ael, n)()
        print(f"PASS  {n}  ({time.time() - t0:.1f} s)")
    except unittest.SkipTest as e:
        skipped += 1
        print(f"SKIP  {n}  ({e})")
    except Exception:
        fails += 1
        print(f"FAIL  {n}  ({time.time() - t0:.1f} s)")
        traceback.print_exc()
ran = len(names) - skipped
print(f"{ran - fails}/{ran} passed" + (f", {skipped} skipped (not checked)" if skipped else ""))
sys.exit(1 if fails else 0)

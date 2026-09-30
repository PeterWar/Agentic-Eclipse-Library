"""Run the tests without pytest: ``python tests/run_tests.py [name_filter]``."""
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_ael  # noqa: E402

flt = sys.argv[1] if len(sys.argv) > 1 else ""
names = [n for n in dir(test_ael) if n.startswith("test_") and flt in n]
fails = 0
for n in names:
    t0 = time.time()
    try:
        getattr(test_ael, n)()
        print(f"PASS  {n}  ({time.time() - t0:.1f} s)")
    except Exception:
        fails += 1
        print(f"FAIL  {n}  ({time.time() - t0:.1f} s)")
        traceback.print_exc()
print(f"{len(names) - fails}/{len(names)} passed")
sys.exit(1 if fails else 0)

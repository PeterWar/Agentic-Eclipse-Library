"""Run without pytest: python tests/run_tests.py [name_filter]."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ael._tests.runner import run
if __name__=='__main__':
    sys.exit(run(sys.argv[1] if len(sys.argv)>1 else ''))

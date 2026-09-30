"""comu43 · Rutes de la V43 d'earthshine (apilat lunar amb TOTS els fotogrames dels dos trens; les curtes manen al limbe) sobre la caixa d'eines V42."""
import sys
from pathlib import Path
HERE43 = Path(__file__).resolve().parent; HERE42 = HERE43.parent / 'v42_20260910'
sys.path.insert(0, str(HERE42))
from comu42 import *   # noqa: F401,F403  (ROOT, CAU42, CAU36, RUNS, comu, f2, log, savejson, CX, CY, RS, COMMON_TO_FINAL, HERE38…)
CAU43 = HERE43 / 'cau'; OUT43 = ROOT / 'output/v43_earthshine_20260910'; REB43 = OUT43 / '4-rebuts'; VIS43 = OUT43 / 'lliurables/vistes'; IAOUT43 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v43_earthshine_20260910')
for _p in (CAU43, REB43, VIS43): _p.mkdir(parents=True, exist_ok=True)

"""comu40 · Rutes de la V40 sobre la caixa d'eines de la V39 (mateix `cau`, mateixos operadors amb els paràmetres de `v39_20260909/cau/tau.json`)."""
import sys
from pathlib import Path
HERE40 = Path(__file__).resolve().parent; HERE39 = HERE40.parent / 'v39_20260909'
sys.path.insert(0, str(HERE39))
from comu39 import *   # noqa: F401,F403  (ROOT, CAU38, CAU39, coords, log, savejson, sha, H, W, RS, CX, CY, …)
OUT40 = ROOT / 'output/v40_20260909'; REB40 = OUT40 / '4-rebuts'; VIS40 = OUT40 / 'lliurables/vistes'; IAOUT40 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v40_20260909')
for _p in (REB40, VIS40): _p.mkdir(parents=True, exist_ok=True)
PC39 = HERE39 / 'purs/cau'

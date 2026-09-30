"""comu42 · Rutes de la V42 sobre la caixa d'eines V38/V39 (mateixa cadena; recomposició de l'apuntament B de la Sony amb la rotació mesurada i
registre dels seus fotogrames llargs; filtres sobre una base sense estrelles; capa d'estrelles de llum mesurada)."""
import sys
from pathlib import Path
HERE42 = Path(__file__).resolve().parent; HERE38 = HERE42.parent / 'v38_20260908'; HERE39 = HERE42.parent / 'v39_20260909'; HERE41 = HERE42.parent / 'v41_20260909'
for _p in (HERE38, HERE39, HERE41): sys.path.insert(0, str(_p))
from comu38 import *   # noqa: F401,F403  (ROOT, CAU38, CAU36, CAU37, CAUF, REB36, RUNS, comu, f2, coords, log, savejson, sha, H, W, RS, CX, CY, COMMON_TO_FINAL…)
CAU42 = HERE42 / 'cau'; OUT42 = ROOT / 'output/v42_20260910'; REB42 = OUT42 / '4-rebuts'; VIS42 = OUT42 / 'lliurables/vistes'; IAOUT42 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v42_20260910')
for _p in (CAU42, REB42, VIS42): _p.mkdir(parents=True, exist_ok=True)
CAU39 = HERE39 / 'cau'; REB41 = ROOT / 'output/v41_20260909/4-rebuts'

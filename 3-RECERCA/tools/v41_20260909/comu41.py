"""comu41 · Rutes de la V41 sobre la caixa d'eines de la V39/V40. La V41 no calcula cap filtre: reassembla capes existents (V39.psb + V38.psb)."""
import sys
from pathlib import Path
HERE41 = Path(__file__).resolve().parent; HERE40 = HERE41.parent / 'v40_20260909'; HERE39 = HERE41.parent / 'v39_20260909'
sys.path.insert(0, str(HERE39)); sys.path.insert(0, str(HERE40))
from comu39 import *   # noqa: F401,F403  (ROOT, CAU38, CAU39, coords, log, savejson, sha, H, W, RS, CX, CY, …)
OUT41 = ROOT / 'output/v41_20260909'; REB41 = OUT41 / '4-rebuts'; VIS41 = OUT41 / 'lliurables/vistes'; IAOUT41 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v41_20260909')
for _p in (REB41, VIS41): _p.mkdir(parents=True, exist_ok=True)

"""comu38 · V38: la franja de l'oest curada a la FONT (màscara lunar per fotograma) + Lluna a l'INICI + projecte complet.
Hereta comu37 (→ comu36 → comu35 → comu34 → comu32): plans_v36 (LUT Sony), farcits A/B, constants V35."""
import os, sys, json, time
from pathlib import Path
HERE38 = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE38.parent / 'v37_20260908'))
import comu37
from comu37 import *
from comu37 import HERE37, CAU37, REB37, VIS37
from comu36 import HERE36, CAU36, REB36
from comu34 import CAU34, HERE34
CAU38 = HERE38 / 'cau'; OUT38 = ROOT / 'output/v38_20260908'; VIS38 = OUT38 / 'lliurables/vistes'; REB38 = OUT38 / '4-rebuts'
IAOUT38 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v38_20260908')
for p in (CAU38, VIS38, REB38, IAOUT38):
    p.mkdir(parents=True, exist_ok=True)
GUARDA_ACTUAL_PX = 2.0; VORA_ACTUAL_PX = 2.0      # f2.GUARDA_LLUNA_PX / VORA_LLUNA_PX vigents (V29…V37)


def upsample(phi_c):
    """(HC,WC) → (H,W) com a b2_recomposicio."""
    a = cv2.resize(np.asarray(phi_c, np.float32), (WC * Q, HC * Q), interpolation=cv2.INTER_LINEAR)
    out = np.empty((H, W), np.float32); out[:HC * Q, :WC * Q] = a
    out[HC * Q:, :WC * Q] = a[-1:, :]; out[:, WC * Q:] = out[:, WC * Q - 1:WC * Q]
    return out

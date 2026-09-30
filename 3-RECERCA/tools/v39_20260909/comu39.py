"""comu39 · V39: soroll dels filtres fora de la corona (guany de Wiener per escala amb el soroll MESURAT), validacions, capes segons Pere.
Hereta comu38 (→ comu37 → … → comu32)."""
import os, sys, json, time
from pathlib import Path
HERE39 = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE39.parent / 'v38_20260908'))
import comu38
from comu38 import *
from comu38 import HERE38, CAU38, REB38, VIS38
CAU39 = HERE39 / 'cau'; OUT39 = ROOT / 'output/v39_20260909'; VIS39 = OUT39 / 'lliurables/vistes'; REB39 = OUT39 / '4-rebuts'
IAOUT39 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v39_20260909')
for p in (CAU39, VIS39, REB39, IAOUT39):
    p.mkdir(parents=True, exist_ok=True)
PC38 = HERE38 / 'purs/cau'


def var_fusio_fina():
    """Variància de la banda fina (DoG 1,5/3 px de ln G) de la FUSIÓ: combinació dels dos trens amb els pesos de la fusió (soroll independent)."""
    wv = np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'); vV = np.load(CAU38 / 'var_vixen_v38.npy', mmap_mode='r'); vS = np.load(CAU38 / 'var_sony_v38.npy', mmap_mode='r')
    wv = np.nan_to_num(np.asarray(wv, np.float32)); vV_ = np.nan_to_num(np.asarray(vV, np.float32)); vS_ = np.nan_to_num(np.asarray(vS, np.float32))
    return (wv * wv * vV_ + (1 - wv) * (1 - wv) * vS_).astype(np.float32)


def lluny_del_forat(m, r, d0=16):
    """Suport SENSE els d0 px que toquen la vora del forat lunar. Mesurat (A2b, 09-09): les dues meitats (fotogrames alternats) hi tenen la vora del
    forat a sub-píxel de distància i, amb el gradient del limbe, ln(E/O) hi val ×32 el rms a 1 px, ×3 fins a 7 px, ×1,2 a 16 px (est, fora de la
    franja): l'estimador de soroll hi és INVÀLID (a 0,98–1,06 R☉ donava 100–200× el soroll d'1,15–1,30 i feia caure el guany en un anell al limbe:
    biaix d'anell P04 0,37→0,62 σ). Només compta la vora del FORAT (fora d'1,3 R☉ es pren com a suport ple): la trampa de la distància a una vora
    sobre suport parcial no hi entra. Conseqüència declarada: dins d'aquests 16 px (la franja de l'oest inclosa) el soroll es pren dels veïns de
    fora (finestra normalitzada): s'hi SUBESTIMA el soroll → menys atenuació → es conserva el detall (i el gra) del limbe."""
    import cv2
    mm = (m | (r > 1.3 * RS)).astype(np.uint8); dt = cv2.distanceTransform(mm, cv2.DIST_L2, 5); return dt >= d0


def dist_vora_suport(m):
    """Distància (px) de cada píxel del suport m a la vora MÉS PROPERA del suport (forat lunar, vora exterior del camp d'un tren, vores de la Sony,
    vora del llenç). V40 (Codex, 09-09): les dues meitats de fotogrames tenen TOTES les vores del seu suport a distància sub-píxel l'una de l'altra, no només
    el forat; ln(E/O) hi val ×13 (vora exterior Vixen) i ×32 (forat) a 0–2 px i torna a 1 cap a 10–16 px. La guarda és per escala: d ≥ max(16, ℓ)."""
    import cv2
    return cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5)

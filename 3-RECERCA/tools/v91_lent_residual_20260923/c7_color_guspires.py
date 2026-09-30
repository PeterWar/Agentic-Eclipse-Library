"""c7 · El color real de les guspires a la foto 76: excés per canal (foto − fons local del mateix canal: obertura 41 px + gaussiana σ 8) als píxels
on la capa 267 hi posa detall (top-hat per sobre del soroll, fora del cos) i cap canal saturat (< 0,95). La 267 de la V91 es va pintar amb el rosa
MITJÀ DEL COS de la protuberància (1,36 · 0,866 · 0,735, normalitzat a lluminància 1): és més blau que la corona i, sumat a sobre, la destenyeix cap
al gris (marques grises de Pere, 00:14). Sortida: C7_COLOR_GUSPIRES.json."""
from pathlib import Path
import json, sys
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v91_lent_residual_20260923'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
Z = np.load(ARREL / '4-RESULTATS/v91_20260923/P1_PROTUBERANCIA.npz'); BX = tuple(int(v) for v in Z['caixa']); E = Z['rgb'].astype(np.float32) / 65535; reg = Z['alfa'].astype(np.float32) / 65535
p = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); F = np.stack([p.channel_box(76, c, BX) for c in range(3)], -1).astype(np.float32) / 65535
ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)); fons = np.stack([cv2.GaussianBlur(cv2.morphologyEx(F[..., c], cv2.MORPH_OPEN, ker), (0, 0), 8) for c in range(3)], -1)
exc = F - fons; Ls = 0.3 * E[..., 0] + 0.59 * E[..., 1] + 0.11 * E[..., 2]
sel = (Ls > np.percentile(Ls[Ls > 0], 50)) & (reg > 0.5) & (F.max(-1) < 0.95)
v = exc[sel]; w = Ls[sel]; mitja = (v * w[:, None]).sum(0) / w.sum(); col = mitja / (0.3 * mitja[0] + 0.59 * mitja[1] + 0.11 * mitja[2])
fonsc = fons[sel].mean(0)
rep = dict(px=int(sel.sum()), exces_mitja=np.round(mitja, 4).tolist(), color_normalitzat_lluminancia_1=np.round(col, 3).tolist(), color_V91=[1.36, 0.866, 0.735],
           fons_foto_mitja=np.round(fonsc, 4).tolist(), quocients=dict(G_R=round(float(mitja[1] / mitja[0]), 3), B_R=round(float(mitja[2] / mitja[0]), 3)),
           exces_percentils_R_G_B={q: np.round(np.percentile(v, q, axis=0), 4).tolist() for q in (25, 50, 75)})
(SORT / 'C7_COLOR_GUSPIRES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); print(json.dumps(rep, ensure_ascii=False))

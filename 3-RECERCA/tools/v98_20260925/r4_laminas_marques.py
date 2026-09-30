"""r4 (V98) · Làmines de revisió: per a cada capa de marques de Pere a V97_Artefactes.psb, el filtre de la V97 amb la marca a sobre (esquerra) i el
mateix filtre de la V98 (dreta), a la caixa de la marca, a escala 1:1 (o 2:1 si la caixa és petita). Transparent = gris fosc.
Sortida: 4-RESULTATS/v98_20260925/laminas/Lxxx_<filtre>.png"""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924'))
from psb69 import PSB
from jutge_comu import Estat
O = ARREL / '4-RESULTATS/v98_20260925/laminas'; O.mkdir(parents=True, exist_ok=True)
S = PSB(str(ARREL / '1-PHOTOSHOP/V97_Artefactes.psb')); E8 = Estat(ARREL / '4-RESULTATS/v98_20260925/estat_v98')
PARELLES = [(313, 54, 'P03 MGN (lupa)'), (301, 55, 'P04 WOW (lupa)'), (314, 56, 'P05 WOW bilateral (lupa)'), (311, 43, 'P02 RHEF (arcs)'), (310, 44, 'P02b RHEF (arcs)'),
            (309, 41, 'P01 NRGF (arcs)'), (306, 42, 'P01b NRGF (arcs)'), (307, 47, '03 ACHF r0 (teulat)'), (304, 51, '04 ACHF micro (vora del limbe)'), (305, 45, 'P02c RHEF local 60 (banda)')]
fet = []
for marca, lid, nom in PARELLES:
    L = S.layer(marca); m = 60; box = (max(L['left'] - m, 0), max(L['top'] - m, 0), min(L['right'] + m, S.width), min(L['bottom'] + m, S.height)); x0, y0, x1, y1 = box
    def filtre_psb():
        g = S.channel_box(lid, 1, box).astype(np.float32) / 65535; a = S.channel_box(lid, -1, box); a = np.ones_like(g) if a is None else a.astype(np.float32) / 65535; return g, a
    g7, a7 = filtre_psb(); g8 = E8.rgb(lid, box); g8 = g8 if g8.ndim == 2 else g8[..., 1]; a8 = E8.dada(lid, box)
    ok = np.concatenate([g7[a7 > 0.99], g8[a8 > 0.99]]); lo, hi = np.percentile(ok, [1, 99]) if ok.size else (0, 1)
    def rgb(g, a):
        v = np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1); v = v * a + 0.12 * (1 - a); return np.dstack([v, v, v])
    mk = np.dstack([S.channel_box(marca, c, box) for c in (0, 1, 2)]).astype(np.float32) / 65535; ma = S.channel_box(marca, -1, box).astype(np.float32) / 65535
    ma = np.clip(ma / max(float(ma.max()), 1e-6), 0, 1)[..., None] * 0.45
    esq = rgb(g7, a7) * (1 - ma) + mk * ma; dre = rgb(g8, a8)
    f = 2 if max(x1 - x0, y1 - y0) < 500 else 1
    im = np.hstack([esq, np.ones((esq.shape[0], 8, 3)), dre]); im = cv2.resize((im * 255).astype(np.uint8), None, fx=f, fy=f, interpolation=cv2.INTER_NEAREST)
    cv2.putText(im, f'V97 + marca {marca}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2); cv2.putText(im, 'V98', (esq.shape[1] * f + 16, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
    nomf = O / f'L{marca}_capa{lid}.png'; cv2.imwrite(str(nomf), im[..., ::-1]); fet.append(dict(marca=marca, capa=lid, nom=nom, caixa=box, fitxer=nomf.name)); print(nomf.name, flush=True)
(O / 'LAMINES.json').write_text(json.dumps(fet, ensure_ascii=False, indent=1))

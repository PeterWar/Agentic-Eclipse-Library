"""d2 (V98) · Punt 1 de Pere: què hi ha dins del disc de presentació de la Lluna (centre 5375,79/3775,98, R 452,98) a la V97:
alfa de la Lluna (258) per distància al limbe i azimut; alfa dels filtres i màscares de Pere dins del disc; pes efectiu dels filtres
sota la vora de la Lluna (alfa_filtre·màscara·opacitat·(1−alfa_Lluna)). Sortida: D2_INTERIOR_LLUNA.json."""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat, LLUNA, RLLUNA
E = Estat(ARREL / '4-RESULTATS/v97_refundacio_20260924/estat_v97'); O = ARREL / '4-RESULTATS/v98_20260925'
box = (4800, 3200, 5960, 4360); x0, y0, x1, y1 = box
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA; th = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) + 360) % 360
aL = E.alfa_efectiva(258, box)
bins = [(-30, -12), (-12, -6), (-6, -4), (-4, -3), (-3, -2), (-2, -1), (-1, -0.5), (-0.5, 0), (0, 0.5), (0.5, 1), (1, 2), (2, 3), (3, 5)]
secs = [(a, a + 30) for a in range(0, 360, 30)]
rep = dict(caixa=box, lluna=dict(centre=LLUNA, R=RLLUNA), alfa_lluna={}, filtres={})
for a0, a1 in secs:
    s = ((th - a0) % 360) < (a1 - a0); rep['alfa_lluna'][f'{a0}-{a1}'] = {f'{b0}..{b1}': round(float(np.mean(aL[s & (d >= b0) & (d < b1)])), 3) for b0, b1 in bins}
for lid in (41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56):
    c = E.capes[lid]; dada = E.dada(lid, box); m = E._llegeix(lid, 'mascara', box, fill=65535 if (c.get('mascara') or {}).get('background') == 255 else 0)
    m = np.ones_like(dada) if m is None else np.asarray(m, np.float32) / 65535
    ef = dada * m * (c['opacitat'] / 255) * (1 - aL) * (1 if c['visible'] else 0)
    r = dict(nom=c.get('nom', ''), mode=c['mode'], visible=c['visible'], opacitat=c['opacitat'])
    for nom_z, z in (('dins_disc_d<-2', d < -2), ('vora_-2..0', (d >= -2) & (d < 0))):
        zl = z & (((th - 90) % 360) < 180)   # meitat esquerra (90–270°)
        zr = z & ~(((th - 90) % 360) < 180)
        r[nom_z] = dict(px_alfa_filtre_gt0_esq=int((dada[zl] > 0).sum()), px_mascara_gt0_esq=int((m[zl] > 0).sum()), mascara_mitjana_esq=round(float(m[zl].mean()), 3),
                        pes_efectiu_max_esq=round(float(ef[zl].max()), 4), px_alfa_filtre_gt0_dreta=int((dada[zr] > 0).sum()), mascara_mitjana_dreta=round(float(m[zr].mean()), 3), pes_efectiu_max_dreta=round(float(ef[zr].max()), 4))
    rep['filtres'][lid] = r; print(lid, r, flush=True)
for k, v in rep['alfa_lluna'].items(): print('Lluna', k, v)
(O / 'D2_INTERIOR_LLUNA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))

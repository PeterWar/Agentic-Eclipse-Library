"""vn4 (V108 · verificador de «negres») · (1) per sectors de 45°, les zones negres amb el cel de referència DINS del marc (5–5,6 R☉) i amb el de
6,5–8,5 R☉ (fora del marc a dalt i a baix), per a la V107 i CEL_TER_Q emulades (L de vn1); on es mou el cel de referència;
(2) on difereix el ràster de la 41/42 del PSB V107 del de filtres_v103 (dins o fora de l'alfa, de la màscara). Sortida: VN4.json"""
import sys, json
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v108_20260926/verifica_negres'))
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917'))
import vn1_psb_i_emulacio as V
from psb69 import PSB
OUT = V.OUT; res = {}
L7 = np.load(OUT / 'L_emul_V107_pas2.npy'); LC = np.load(OUT / 'L_emul_CEL_TER_Q_pas2.npy')
for nomref, (ra, rb, vc) in {'cel_6.5-8.5': (6.5, 8.5, V.VALID_CEL), 'cel_dins_marc_5-5.6': (5.0, 5.6, V.marc & ~V.lluna)}.items():
    for nom, L in (('V107', L7), ('CEL_TER_Q', LC)):
        Ls = cv2.GaussianBlur(L, (0, 0), 3.0); cv, sky, _ = V.cel_sector(Ls, vc & (L > 1e-4), 36, ra, rb); z = V.ZONA & (L > 1e-4); neg = z & (Ls < sky)
        d = {f'{s}-{s+45}': round(float(neg[z & (V.th >= s) & (V.th < s + 45)].mean()), 4) for s in range(0, 360, 45)}
        d['cel_sector_90'] = float(cv[9]); d['cel_sector_270'] = float(cv[27]); d['cel_sector_0'] = float(cv[0]); d['cel_sector_180'] = float(cv[18])
        for a, b in ((2, 3), (3, 4.5)):
            m = z & (V.r >= a) & (V.r < b); d[f'banda_{a}-{b}'] = round(float(neg[m].mean()), 4)
        res[f'{nomref}|{nom}'] = d
# mediana de L a 3–4,5 R☉ per sector (el que es veu) V107 → CEL_TER_Q
res['mediana_L_3-4.5_per_sector'] = {f'{s}-{s+45}': [float(np.median(L7[V.ZONA & (V.r >= 3) & (V.th >= s) & (V.th < s + 45)])), float(np.median(LC[V.ZONA & (V.r >= 3) & (V.th >= s) & (V.th < s + 45)]))] for s in range(0, 360, 45)}
# ràster PSB vs filtres_v103
psb = PSB(str(R0 / '1-PHOTOSHOP/V107.psb')); box = (0, 0, V.W, V.H)
for lid, tag in ((41, 'P01_NRGF'), (42, 'P01_NRGF_extrap')):
    g = psb.channel_box(lid, 1, box).astype(np.int32); o = np.load(V.ORIG / f'{tag}_u16.npy').astype(np.int32); al = psb.channel_box(lid, -1, box)
    mk = psb.channel_box(lid, -2, box, fill=0); l = psb.layer(lid)
    d = np.abs(g - o); ins = al > 0
    res[f'raster_psb_{lid}'] = dict(bbox_capa=[l['left'], l['top'], l['right'], l['bottom']], px_dif_gt2_dins_alfa=int((d[ins] > 2).sum()), px_dif_gt2_fora_alfa=int((d[~ins] > 2).sum()),
                                    max_dif_dins_alfa=int(d[ins].max()), px_alfa=int(ins.sum()),
                                    px_dif_gt2_dins_alfa_i_mascara=int((d[ins & (mk > 0)] > 2).sum()) if mk is not None else None)
    ys, xs = np.nonzero(ins & (d > 2))
    if len(ys): res[f'raster_psb_{lid}']['caixa_difs_dins_alfa'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
(OUT / 'VN4.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print(json.dumps(res, ensure_ascii=False, indent=1))

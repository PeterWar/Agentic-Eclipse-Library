"""c5 (V105, Claude, 26-09-2026) · Visualització de la cobertura del limbe lunar: quins fotogrames van veure la corona arran de la vora de la Lluna
de presentació lluny de la seva pròpia Lluna, per angle, i què passaria amb una Lluna de presentació d'un altre instant.
Dades: els limb_frames sense llindar (Codex, 26-09): centre de la Lluna de cada fotograma a partir del seu mapa de distància al limbe del model
(com a a3d.dreal), la silueta d'ordre 2 de la V99 (vora real = cercle + e(PA)) i el pes LDIC per marcar les exposicions que saturen arran del limbe.
Sortida: 4-RESULTATS/v105_limbe_20260926/visualitzacio/COBERTURA_DEL_LIMBE.html (autònoma, sense dependències) i COBERTURA_DADES.json.
Ús: [V105_LF=<limb_frames>] c5_visualitzacio_cobertura.py"""
import os, json, numpy as np, cv2
from pathlib import Path
R0 = Path(__file__).resolve().parents[3]
LF = Path(os.environ.get('V105_LF', '/private/tmp/v105_raw_pilot_20260926/no_floor_all67'))
O = R0 / '4-RESULTATS/v105_limbe_20260926/visualitzacio'; O.mkdir(parents=True, exist_ok=True)
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
geo = json.loads((R0 / '4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
Rm = float(meta['radius_model']); DR = Rm - R
sil = np.load(R0 / '4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); SPA = np.asarray(sil['pa'], float); SE = np.asarray(sil['e'], float)
e = lambda a: np.interp(np.asarray(a) % 360, SPA, SE, period=360)
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
pas = np.arange(0, 360, 2.0); th = np.radians(pas)
F = []
for j, f in enumerate(fr):
    D = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(D); iy, ix = hb // 2, wb - 100
    cxj = ix + bx0 - (D[iy, ix] + Rm) * gx[iy, ix]; cyj = iy + by0 - (D[iy, ix] + Rm) * gy[iy, ix]
    # saturació: on la geometria és bona (D_real ≥ 2 px) a 1–3 px de la vora real de la Lluna de presentació, fracció d'angles amb pes zero
    nb = nz = 0
    for d in (1.0, 2.0, 3.0):
        r = R + e(pas) + d; px = cx + r * np.cos(th); py = cy - r * np.sin(th)
        w = cv2.remap(np.ascontiguousarray(wt[j, :, :, 1], np.float32), (px - bx0).astype(np.float32)[None, :], (py - by0).astype(np.float32)[None, :], cv2.INTER_NEAREST)[0]
        a = np.degrees(np.arctan2(-(py - cyj), px - cxj)); Dr = np.hypot(px - cxj, py - cyj) - R - e(a)
        ok = Dr >= 2; nb += int(ok.sum()); nz += int((ok & (w <= 0)).sum())
    ex = f['exposure']; lab = f'1/{round(1 / ex)} s' if ex < 1 else f'{ex:g} s'
    F.append(dict(t=round(f['time'], 2), e=lab, dx=round(float(cxj - cx), 3), dy=round(float(-(cyj - cy)), 3), sat=bool(nb > 0 and nz > 0.5 * nb)))
fr0 = int(np.argmin([abs(f['t'] - 22.3) for f in F]))
dades = dict(R=round(R, 4), e=[round(float(v), 4) for v in e(np.arange(360))], f=F, fr0=fr0,
             font=dict(limb_frames=str(LF), silueta='4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz', geometria='4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json'))
(O / 'COBERTURA_DADES.json').write_text(json.dumps(dades, ensure_ascii=False, indent=1))
html = (Path(__file__).parent / 'c5_cobertura_plantilla.html').read_text().replace('/*DADES*/null', json.dumps({k: v for k, v in dades.items() if k != 'font'}, separators=(',', ':')))
(O / 'COBERTURA_DEL_LIMBE.html').write_text(html)
print('fotogrames', len(F), '· saturats', sum(f['sat'] for f in F), '·', O / 'COBERTURA_DEL_LIMBE.html')

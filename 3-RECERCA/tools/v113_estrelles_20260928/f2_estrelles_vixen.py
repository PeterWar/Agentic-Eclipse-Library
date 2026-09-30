"""f2 · V113 (Claude, 28-09-2026): on té la Vixen cada estrella (llenç), per treure-les de les fonts «sense estrelles».
Diagnosi (auditoria d'inventari): la base conserva «fantasmes» a 10–12 px de S02, S16, S23, S25, S29… que són les estrelles de l'apilat Vixen,
registrat amb un gir d'~0,1–0,2° respecte de la Sony i del cel: el D4 treu cada estrella amb un model centrat a la posició canònica (±6–9 px) i
la còpia de la Vixen hi queda. Aquí es mesura, a l'apilat Vixen de la fusió (flat2d_v5), el pic de cada estrella a menys de 20 px de la posició
canònica; s'ajusta un model afí del desplaçament amb les ben mesurades i es fa servir el model on la mesura és feble.
Estrelles: les 52 que el D4 ja treu + les del S22 que no hi són (per posició). Es proposa una extracció addicional:
  · còpia Vixen: on |desplaçament| > 2,5 px i el pes de la Vixen a la fusió hi és > 0,02 (si no, la fusió no la conté);
  · canònica: per a les del S22 que el D4 no treia (llum d'estrella que es quedava a la base sota la 202).
Sortida: 4-RESULTATS/v113_estrelles_20260928/fantasmes/EXTRA_ESTRELLES.json + F2_REBUT.json (mesures, model, controls)."""
import json, time
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[3]
O = R / '4-RESULTATS/v113_estrelles_20260928/fantasmes'; O.mkdir(parents=True, exist_ok=True)
S22 = json.loads((R / '4-RESULTATS/v65_pere_estrelles_20260914/S22_final_catalog.json').read_text())['stars']
D4 = json.loads((R / '4-RESULTATS/v112_claude_20260928/fonts_v113_vora/fusio/d4/products/D4_sources.json').read_text())['selected']
V = np.load(R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/vixen_total.npy', mmap_mode='r')
Vd = np.load(R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/vixen_den.npy', mmap_mode='r')
WV = np.load(R / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/weight_vixen_v42.npy', mmap_mode='r')
SUN = np.array([5361.77, 3775.75]); t0 = time.time()
# llista d'estrelles: D4 (enteres) + S22 no presents
estrelles = []
for r in D4:
    s = r['star']; m = min(S22, key=lambda q: np.hypot(q['x'] - s['x'], q['y'] - s['y']))
    fx, fy = (m['x'], m['y']) if np.hypot(m['x'] - s['x'], m['y'] - s['y']) < 3 else (float(s['x']), float(s['y']))
    estrelles.append(dict(id=m['id'] if np.hypot(m['x'] - s['x'], m['y'] - s['y']) < 3 else s.get('TYC', 'D4'), x=fx, y=fy, a_D4=True, V=m['V']))
for m in S22:
    if all(np.hypot(m['x'] - e['x'], m['y'] - e['y']) > 5 for e in estrelles): estrelles.append(dict(id=m['id'], x=m['x'], y=m['y'], a_D4=False, V=m['V']))
yy, xx = np.mgrid[-32:33, -32:33]; rr = np.hypot(xx, yy)
def mesura(x, y, rad=20):
    ix, iy = int(round(x)), int(round(y))
    if not (40 <= ix < 10551 - 40 and 40 <= iy < 7506 - 40): return None
    w = np.asarray(V[iy - 32:iy + 33, ix - 32:ix + 33, 1], np.float64); d = np.asarray(Vd[iy - 32:iy + 33, ix - 32:ix + 33])
    if (d <= 0).any() or not np.isfinite(w).all(): return None
    bg = np.median(w[rr > 26]); mad = 1.4826 * np.median(np.abs(w[rr > 26] - bg)) + 1e-12
    c = np.where(rr <= rad, w - bg, -np.inf); k = np.unravel_index(np.argmax(c), c.shape); pk = c[k]
    wt = np.clip(w - bg, 0, None) * (np.hypot(xx - xx[k], yy - yy[k]) <= 3)
    cx = (xx * wt).sum() / wt.sum() + ix; cy = (yy * wt).sum() / wt.sum() + iy
    return dict(x=float(cx), y=float(cy), snr=float(pk / mad), dx=float(cx - x), dy=float(cy - y))
for e in estrelles: e['vixen'] = mesura(e['x'], e['y'])
bons = [e for e in estrelles if e['vixen'] and e['vixen']['snr'] > 6]
def dissenya(P):
    # SEMBLANÇA del desplaçament (gir petit + escala + translació), relativa al Sol: dx = e·X − g·Y + tx, dy = g·X + e·Y + ty
    X = P[:, 0] - SUN[0]; Y = P[:, 1] - SUN[1]; z = np.zeros(len(P)); u = np.ones(len(P))
    return np.stack([np.c_[X, -Y, u, z], np.c_[Y, X, z, u]], 1)          # (n, 2, 4)
P = np.array([[e['x'], e['y']] for e in bons]); Dxy = np.array([[e['vixen']['dx'], e['vixen']['dy']] for e in bons])
us = np.ones(len(bons), bool)
for _ in range(6):
    Aa = dissenya(P[us]).reshape(-1, 4); cf = np.linalg.lstsq(Aa, Dxy[us].reshape(-1), rcond=None)[0]
    res = Dxy - dissenya(P) @ cf; nus = np.hypot(*res.T) < 3.0
    if (nus == us).all(): break
    us = nus
print(f'semblança del desplaçament Vixen: {us.sum()}/{len(bons)} estrelles (S/N>6), rms {np.sqrt((res[us]**2).sum(1).mean()):.2f} px', flush=True)
# rotació i escala equivalents del model
rot = np.degrees(cf[1]); esc = 1 + cf[0]
extra = []; taula = []
for e in estrelles:
    pred = dissenya(np.array([[e['x'], e['y']]])) @ cf; pdx, pdy = float(pred[0, 0]), float(pred[0, 1])
    m = e['vixen']; usa_mesura = bool(m and m['snr'] > 6 and np.hypot(m['dx'] - pdx, m['dy'] - pdy) < 3.0)
    vx, vy = (m['x'], m['y']) if usa_mesura else (e['x'] + pdx, e['y'] + pdy)
    ix, iy = int(round(vx)), int(round(vy)); wv = float(np.asarray(WV[iy, ix])) if (0 <= ix < 10551 and 0 <= iy < 7506) else 0.0
    desp = float(np.hypot(vx - e['x'], vy - e['y']))
    fila = dict(id=e['id'], canonica=[e['x'], e['y']], vixen=[vx, vy], desplacament_px=desp, font='mesura' if usa_mesura else 'model', snr_vixen=(m or {}).get('snr'), pes_vixen=wv, a_D4=e['a_D4'])
    taula.append(fila)
    if desp > 2.5 and wv > 0.02: extra.append(dict(x=int(round(vx)), y=int(round(vy)), xf=vx, yf=vy, vixen_copy=True, copia_de=e['id'], V=e['V']))
    if not e['a_D4']: extra.append(dict(x=int(round(e['x'])), y=int(round(e['y'])), xf=e['x'], yf=e['y'], vixen_copy=False, canonica_nova=True, copia_de=e['id'], V=e['V']))
# control: pics als llocs predits però amb el desplaçament girat 180° (on no hi ha d'haver res)
ctrl = [mesura(e['x'] - (t['vixen'][0] - e['x']), e['y'] - (t['vixen'][1] - e['y']), rad=3) for e, t in zip(estrelles, taula) if t['desplacament_px'] > 2.5]
ctrl = [c['snr'] for c in ctrl if c]
rep = dict(estrelles=len(estrelles), a_D4=sum(e['a_D4'] for e in estrelles), mesurades_bones=len(bons), model=dict(tipus='semblança del desplaçament respecte del Sol', coef=cf.tolist(), rms_px=float(np.sqrt((res[us] ** 2).sum(1).mean())), rotacio_equivalent_graus=float(rot), escala_equivalent=float(esc), n=int(us.sum())),
           extraccions_afegides=dict(copies_vixen=sum(1 for x in extra if x['vixen_copy']), canoniques_noves=sum(1 for x in extra if not x['vixen_copy'])),
           control_desplacament_invertit_snr=dict(n=len(ctrl), p50=float(np.median(ctrl)) if ctrl else None, max=float(np.max(ctrl)) if ctrl else None),
           taula=taula, segons=round(time.time() - t0, 1))
(O / 'EXTRA_ESTRELLES.json').write_text(json.dumps(extra, indent=1)); (O / 'F2_REBUT.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in rep.items() if k != 'taula'}, indent=1, ensure_ascii=False))
for t in sorted(taula, key=lambda t: -t['desplacament_px'])[:14]: print(t['id'], [round(v, 1) for v in t['vixen']], round(t['desplacament_px'], 1), t['font'], round(t['snr_vixen'] or 0, 1), round(t['pes_vixen'], 3))

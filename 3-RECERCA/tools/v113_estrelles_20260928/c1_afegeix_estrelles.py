"""c1 · V113 (Claude, 28-09-2026): les estrelles que FALTEN — reals (Tycho-2), amb senyal repetit a les NOSTRES dades als dos apuntaments de la
Sony, cap control nul que hi arribi, i acceptades per dos verificadors escèptics — pintades amb la MATEIXA recepta de la V65 (S22_final_catalog.json):
  · gaussiana circular integrada al píxel, σ = 1,5 px del llenç, a la posició de catàleg transportada al llenç;
  · pic = 0,74 · (F / F_max)^0,55, amb F el flux verd natiu de la Sony en les unitats del S22 i F_max el de l'estrella més brillant;
  · color: display_RGB = pic · cromaticitat^(1/γ), γ = 563/256.
F es MESURA als RAW de la Sony (fotometria d'apertura forçada al verd CFA, fotogrames llargs dels dos apuntaments) i es passa a unitats del S22 amb
la relació lineal ajustada a les 60 estrelles mesurades igual (sense cap supòsit de magnitud). La cromaticitat, que a S/N 6–8 no es pot mesurar
bé, és la mediana de les 60 amb B−V més semblant (Tycho) — declarat.
Norma de Pere «cada canvi, una capa»: les estrelles noves van en una CAPA NOVA (Sobreexposició lineal, com la 202) just damunt de la 202, que no
es toca. Entrada: JSON amb [{id, x, y, V, BV}] (posició al llenç). Sortida: 4-RESULTATS/v113_estrelles_20260928/estrelles/L_estrelles_noves.npz
(R,G,B,A,bbox: marc ajustat a les estrelles, opac on hi ha llum i TRANSPARENT a la resta — revisió de les 18 h: la primera versió, negra i opaca
a tot el llenç, feia opac el document i canviava 1.173 píxels del limbe lunar fins a un 0,1 %; guardada com a L_estrelles_noves_opaca.npz) i C1_REBUT.json.
Ús: c1_afegeix_estrelles.py noves.json"""
import sys, json
from pathlib import Path
import numpy as np, rawpy
from scipy.special import erf
R = Path(__file__).resolve().parents[3]
O = R / '4-RESULTATS/v113_estrelles_20260928/estrelles'; O.mkdir(parents=True, exist_ok=True)
EST = Path('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ac3c039a-6c03-41d3-b175-986d28f999ef/scratchpad/estrelles/nostres')
S22 = json.loads((R / '4-RESULTATS/v65_pere_estrelles_20260914/S22_final_catalog.json').read_text())['stars']
noves = json.loads(Path(sys.argv[1]).read_text())
RAWS = ['DSC06993', 'DSC06987', 'DSC06996', 'DSC06999', 'DSC06984']
G = 563.0 / 256.0
def inv_q(q, X, Y):
    a, b, tx, ty = q; d = a * a + b * b; u, v = X - tx, Y - ty
    return (a * u + b * v) / d, (-b * u + a * v) / d
def fot(img, x, y, r_ap=6.0, r1=10.0, r2=16.0):
    ix, iy = int(round(x)), int(round(y)); H, W = img.shape
    if not (20 <= ix < W - 20 and 20 <= iy < H - 20): return None
    w = img[iy - 18:iy + 19, ix - 18:ix + 19].astype(np.float64); yy, xx = np.mgrid[iy - 18:iy + 19, ix - 18:ix + 19]
    verd = ((yy % 2) + (xx % 2)) == 1                       # RGGB: G1 (0,1) i G2 (1,0)
    r = np.hypot(xx - x, yy - y); an = verd & (r >= r1) & (r < r2); ap = verd & (r < r_ap)
    if (w[ap] >= 15500).any(): return None
    bg = np.median(w[an]); sig = 1.4826 * np.median(np.abs(w[an] - bg))
    fl = (w[ap] - bg).sum() * 2.0; err = sig * np.sqrt(ap.sum()) * 2.0
    return fl, err
mesures = {}
for nom in RAWS:
    q = json.loads((EST / f'm3_{nom}.json').read_text())['q']
    with rawpy.imread(str(R / f'0-RAW/Sony A7RIIIA 300mm/{nom}.ARW')) as rw: img = rw.raw_image.astype(np.float32) - 512.0
    for s in S22 + noves:
        x, y = inv_q(q, s['x'], s['y']); m = fot(img, x, y)
        if m: mesures.setdefault(s['id'], {})[nom] = m
# flux combinat per estrella: mitjana ponderada per fotograma, escalant cada fotograma a DSC06993 amb les 60 (mediana dels quocients)
esc = {}
for nom in RAWS:
    rat = [mesures[s['id']]['DSC06993'][0] / mesures[s['id']][nom][0] for s in S22 if s['id'] in mesures and 'DSC06993' in mesures[s['id']] and nom in mesures[s['id']] and mesures[s['id']][nom][0] > 5 * mesures[s['id']][nom][1] and mesures[s['id']]['DSC06993'][0] > 5 * mesures[s['id']]['DSC06993'][1]]
    esc[nom] = float(np.median(rat)) if rat else None
def combinat(sid):
    v = [(mesures[sid][n][0] * esc[n], mesures[sid][n][1] * esc[n]) for n in mesures.get(sid, {}) if esc.get(n)]
    if not v: return None
    f = np.array([a for a, _ in v]); e = np.array([b for _, b in v]); w = 1 / e ** 2
    return float((f * w).sum() / w.sum()), float(1 / np.sqrt(w.sum())), len(v)
# calibratge a unitats del S22 (recta per l'origen, robust, estrelles amb S/N combinat > 10)
X = []; Y = []
for s in S22:
    c = combinat(s['id'])
    if c and c[0] > 10 * c[1]: X.append(c[0]); Y.append(s['green_flux_sony_units'])
X = np.array(X); Y = np.array(Y); k = np.median(Y / X); us = np.abs(np.log(Y / (k * X))) < 0.5
k = float((X[us] * Y[us]).sum() / (X[us] ** 2).sum()); disp = float(np.std(np.log(Y[us] / (k * X[us]))))
Fmax = max(s['green_flux_sony_units'] for s in S22)
BV22 = np.array([s['BV'] if s['BV'] is not None else np.nan for s in S22]); CH = np.array([s['linear_AdobeRGB_chromaticity'] for s in S22])
rgb = np.zeros((7506, 10551, 3), np.float64)
def gauss_px(x0, y0, sig=1.5, rad=10):
    ix, iy = int(round(x0)), int(round(y0)); xs = np.arange(ix - rad, ix + rad + 1); ys = np.arange(iy - rad, iy + rad + 1)
    gx = 0.5 * (erf((xs + 0.5 - x0) / (np.sqrt(2) * sig)) - erf((xs - 0.5 - x0) / (np.sqrt(2) * sig)))
    gy = 0.5 * (erf((ys + 0.5 - y0) / (np.sqrt(2) * sig)) - erf((ys - 0.5 - y0) / (np.sqrt(2) * sig)))
    g = np.outer(gy, gx); return g / g.max(), (ys[0], ys[-1] + 1, xs[0], xs[-1] + 1)
# control de la recepta: amb aquesta gaussiana, el pic de les 60 és el display_RGB_peak del S22
rebut = dict(recepta='V65 S22: σ 1,5 px; pic = 0,74·(F/Fmax)^0,55; RGB = pic·croma^(1/γ)', calibratge=dict(k_S22_per_unitat_mesura=k, dispersio_ln=disp, n=int(us.sum()), escales_fotograma=esc), estrelles=[])
for s in noves:
    c = combinat(s['id']); assert c, s
    # si l'entrada porta F_S22 (flux verificat amb filtre adaptat, o relació declarada), mana sobre l'apertura simple (massa sorollosa a S/N < 5)
    F = float(s['F_S22']) if 'F_S22' in s else k * c[0]; pk = 0.74 * (max(F, 0) / Fmax) ** 0.55
    near = np.argsort(np.abs(np.nan_to_num(BV22, nan=99) - s['BV']))[:5]; chroma = np.median(CH[near], axis=0); chroma = chroma / chroma.max()
    disp_rgb = pk * np.clip(chroma, 0, 1) ** (1 / G)
    g, (y0, y1, x0, x1) = gauss_px(s['x'], s['y'])
    zona = rgb[y0:y1, x0:x1]
    for ch in range(3): zona[..., ch] = zona[..., ch] + disp_rgb[ch] * g
    rebut['estrelles'].append(dict(id=s['id'], x=s['x'], y=s['y'], V=s['V'], BV=s['BV'], apertura_simple=dict(flux=c[0], error=c[1], fotogrames=c[2], snr=c[0] / c[1], F_S22=k * c[0]),
                                   F_S22=F, font_flux=s.get('font_flux', 'apertura simple'), font_posicio=s.get('font_posicio'), pic=pk, display_RGB=disp_rgb.tolist(), croma=chroma.tolist()))
    print(s['id'], f"S/N {c[0]/c[1]:.1f} ({c[2]} fotogrames)  F {F:.1f}  pic {pk:.3f}  RGB {np.round(disp_rgb,3)}", flush=True)
# referència: estrelles de les 60 de magnitud semblant
for sid in ('S47', 'S45', 'S53', 'S56', 'S35', 'S37'):
    s = next(t for t in S22 if t['id'] == sid); c = combinat(sid)
    print('ref', sid, 'V', s['V'], 'F_S22', round(s['green_flux_sony_units'], 1), 'F_mesurat→S22', round(k * c[0], 1) if c else None, 'pic', s['display_peak'])
out = np.clip(np.round(rgb * 65535), 0, 65535).astype(np.uint16)
llum = (out > 0).any(-1); ys, xs = np.nonzero(llum); x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
A = np.where(llum, 65535, 0).astype(np.uint16)          # opaca només on hi ha llum: fora, la capa no existeix (no toca l'alfa del document)
np.savez_compressed(O / 'L_estrelles_noves.npz', R=out[y0:y1, x0:x1, 0], G=out[y0:y1, x0:x1, 1], B=out[y0:y1, x0:x1, 2], A=A[y0:y1, x0:x1], bbox=np.array([x0, y0, x1, y1]))
rebut['pixels_amb_llum'] = int(llum.sum()); rebut['marc'] = [x0, y0, x1, y1]
(O / 'C1_REBUT.json').write_text(json.dumps(rebut, indent=1, ensure_ascii=False)); print('píxels amb llum', rebut['pixels_amb_llum'], 'calibratge k', round(k, 5), 'dispersió', round(disp, 3), 'n', int(us.sum()))

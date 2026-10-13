"""c1b · Encaix mesurat de la final contra SDO/AIA (substitueix el bucle lent de c1).
Senyals comparats a l'anell fora de la Lluna:
  - protuberàncies: «rosat» de la final ((R−G)+(B−G), passa-alt) contra AIA 304 (log, passa-alt), r 1,00–1,15 R☉;
  - corona baixa: lluminància de la final (passa-alt) contra AIA 171/193/211 (log, passa-alt), r 1,03–1,28 R☉.
Es busca el desplaçament (Δx, Δy) de l'AIA al marc de la final que maximitza la correlació de Pearson (graella entera ±10 px
i després subpíxel ±1 px a 0,1). Δ > 0 vol dir que l'estructura de la final és a +Δ respecte d'on la posa la geometria.
També es fa per sectors d'angle (la protuberància gran domina el total) i amb el centre per estrelles."""
import json, sys
import numpy as np
from scipy import ndimage as nd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *

fin = carrega_final(); gF = geo_final('efemeride')
lluna = np.array(GEO['lluna_px']); RL = GEO['R_lluna_px']
M = int(round(1.40 * gF.R)); x0, y0 = int(round(gF.cx)) - M, int(round(gF.cy)) - M
crop = np.asarray(fin[y0:y0 + 2 * M + 1, x0:x0 + 2 * M + 1]).astype(np.float32) / 65535.0
Rf, Gf, Bf = crop[..., 0], crop[..., 1], crop[..., 2]
Lf = 0.2974 * Rf + 0.6273 * Gf + 0.0753 * Bf; rosat = (Rf - Gf) + (Bf - Gf)
sh = crop.shape[:2]; yy, xx = np.mgrid[0:sh[0], 0:sh[1]]
dins_lluna = np.hypot(xx + x0 - lluna[0], yy + y0 - lluna[1]) < RL + 2.0
g0 = Geo('retall', gF.cx - x0, gF.cy - y0, gF.R, gF.n, gF.e, gF.data, gF.obs)
r0, pa0 = g0.polar(xx, yy)

cache = RES / 'C1_aia_al_marc.npz'
if cache.exists():
    z = np.load(cache); aia = {k: z[k] for k in z.files}
else:
    aia = {}
    for ona in ['0304', '0171', '0193', '0211']:
        for hh in ['1828', '1830']:
            d, g = carrega_aia(hh, ona); aia[f'{ona}_{hh}'] = a_marc(d, g, g0, sh)
    np.savez_compressed(cache, **aia, x0=x0, y0=y0)

def pas_alt(a, s=15):
    a = np.nan_to_num(a.astype(np.float32)); return a - nd.uniform_filter(nd.median_filter(a, size=5), size=s)
def logp(a, eps): return np.log10(np.clip(a, eps, None))

def corr_desplacada(A, B, m, dx, dy):
    As = nd.shift(A, (dy, dx), order=1, mode='nearest')
    a, b = As[m], B[m]; a = a - a.mean(); b = b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))

def cerca(A, B, m, rang=10):
    best = (-2, 0, 0)
    for dy in range(-rang, rang + 1):
        for dx in range(-rang, rang + 1):
            c = corr_desplacada(A, B, m, dx, dy)
            if c > best[0]: best = (c, dx, dy)
    c, bx, by = best
    c2, bx2, by2 = c, float(bx), float(by)
    for dy in np.arange(by - 1, by + 1.001, 0.1):
        for dx in np.arange(bx - 1, bx + 1.001, 0.1):
            cc = corr_desplacada(A, B, m, dx, dy)
            if cc > c2: c2, bx2, by2 = cc, float(dx), float(dy)
    return c2, bx2, by2, corr_desplacada(A, B, m, 0, 0)

res = {}
fora = ~dins_lluna
casos = [('304_protuberancies', '0304', rosat, (1.00, 1.15), 0.02),
         ('171_corona', '0171', Lf, (1.03, 1.28), 0.5), ('193_corona', '0193', Lf, (1.03, 1.28), 0.5), ('211_corona', '0211', Lf, (1.03, 1.28), 0.2)]
for nom, ona, F, (ra, rb), eps in casos:
    B = pas_alt(F)
    for hh in ['1828', '1830']:
        A = pas_alt(logp(aia[f'{ona}_{hh}'], eps))
        m = fora & (r0 >= ra) & (r0 <= rb) & np.isfinite(aia[f'{ona}_{hh}'])
        c, dx, dy, c00 = cerca(A, B, m)
        res[f'{nom}_{hh}'] = dict(rho=c, rho_0=c00, dx_px=dx, dy_px=dy, dx_arcsec=dx * GEO['arcsec_px'], dy_arcsec=dy * GEO['arcsec_px'], n_px=int(m.sum()))
        print(f"{nom} {hh}: ρ màx {c:.3f} a Δ=({dx:+.1f},{dy:+.1f}) px = ({dx*GEO['arcsec_px']:+.1f}″,{dy*GEO['arcsec_px']:+.1f}″); ρ a Δ=0 {c00:.3f}; {m.sum()} px")

# protuberàncies per sectors (cada protuberància pel seu compte)
B = pas_alt(rosat); A = pas_alt(logp(aia['0304_1828'], 0.02))
for nom, (p1, p2) in {'gran_est_95-140': (95, 140), 'filet_25-55': (25, 55), 'oest_260-295': (260, 295), 'resta': (140, 260)}.items():
    m = fora & (r0 >= 1.0) & (r0 <= 1.15) & (pa0 >= p1) & (pa0 < p2)
    c, dx, dy, c00 = cerca(A, B, m, rang=8)
    res[f'304_sector_{nom}'] = dict(rho=c, rho_0=c00, dx_px=dx, dy_px=dy, n_px=int(m.sum()))
    print(f"304 sector {nom}: ρ {c:.3f} a Δ=({dx:+.1f},{dy:+.1f}) px; ρ(0) {c00:.3f}")

gS = geo_final('estrelles')
res['nota'] = ("Δ = desplaçament que cal aplicar a l'AIA (remostrejada amb el centre per efemèride) per encaixar-la a la final. "
               f"El centre per estrelles és a ({gS.cx - gF.cx:+.2f}, {gS.cy - gF.cy:+.2f}) px del de l'efemèride.")
json.dump(res, open(RES / 'C1_ENCAIX.json', 'w'), indent=1)
print(res['nota'])

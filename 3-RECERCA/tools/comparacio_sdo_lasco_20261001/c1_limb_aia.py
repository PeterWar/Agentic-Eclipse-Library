"""c1 · La final contra SDO/AIA a la vora del Sol (1,0–1,3 R☉): protuberàncies (304 Å) i corona baixa (171, 193, 211 Å).
1. Remostreja cada AIA al marc de la final (retall ±1,40 R☉ al voltant del Sol, escala nativa de la final).
2. Desplegats polars (PA 0–360°, r 0,98–1,30 R☉) de la final i de cada AIA.
3. Mesura de l'encaix: correlació del senyal de protuberància (final: «rosat» = (R−G)+(B−G); AIA 304) en el desplegat,
   fora de la Lluna, com a desplaçament (Δx, Δy) del centre del Sol. Dues vies de centre (efemèride i estrelles).
Sortides a 3-RECERCA/resultats/comparacio_sdo_lasco_20261001/ (vistes/ i C1_*.json)."""
import json, math, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *

fin = carrega_final()
H, W = fin.shape[:2]
gF = geo_final('efemeride'); gS = geo_final('estrelles')
lluna = np.array(GEO['lluna_px']); RL = GEO['R_lluna_px']
print(f"final {W}×{H}; Sol (efem.) ({gF.cx:.2f},{gF.cy:.2f}), (estrelles) ({gS.cx:.2f},{gS.cy:.2f}); R☉ {gF.R:.2f} px; Lluna ({lluna[0]:.1f},{lluna[1]:.1f}) R {RL:.1f}")

# ---------------- retall de la final al voltant del Sol (±1,40 R☉)
M = int(round(1.40 * gF.R)); x0, y0 = int(round(gF.cx)) - M, int(round(gF.cy)) - M
crop = np.asarray(fin[y0:y0 + 2 * M + 1, x0:x0 + 2 * M + 1]).astype(np.float32) / 65535.0
Rf, Gf, Bf = crop[..., 0], crop[..., 1], crop[..., 2]
Lf = 0.2974 * Rf + 0.6273 * Gf + 0.0753 * Bf
rosat = (Rf - Gf) + (Bf - Gf)
yy, xx = np.mgrid[0:crop.shape[0], 0:crop.shape[1]]
dins_lluna = np.hypot(xx + x0 - lluna[0], yy + y0 - lluna[1]) < RL + 1.0
gcrop = Geo('final retall', gF.cx - x0, gF.cy - y0, gF.R, gF.n, gF.e, gF.data, gF.obs)

# ---------------- AIA al marc del retall
aia = {}
for ona in ['0304', '0171', '0193', '0211']:
    for hh in ['1828', '1830']:
        d, g = carrega_aia(hh, ona)
        aia[(ona, hh)] = (a_marc(d, g, gcrop, crop.shape[:2], ordre=1), g)
        print(f"AIA {ona} {hh}: T_OBS {g.data}; R☉ {g.R:.2f} px; centre ({g.cx:.1f},{g.cy:.1f})")

# ---------------- vistes cartesianes: final | AIA 304 | AIA 171/193/211 (RGB)
def escala_log(a, p0=1, p1=99.8):
    v = np.log10(np.clip(a, 1e-3, None)); m = np.isfinite(v)
    lo, hi = np.percentile(v[m], [p0, p1]); return a8(v, lo, hi)
r_crop, pa_crop = gcrop.polar(xx, yy)
fora = r_crop > 1.0
vF = (np.clip(crop, 0, 1) * 255).astype(np.uint8)
a304 = aia[('0304', '1828')][0]
v304 = escala_log(np.where(fora, a304, np.nan), 2, 99.9)
v304 = np.where(fora, v304, (escala_log(a304, 1, 99.9) * 0.45).astype(np.uint8))
rgbE = np.dstack([escala_log(aia[('0211', '1828')][0]), escala_log(aia[('0193', '1828')][0]), escala_log(aia[('0171', '1828')][0])])
sz = 1100
tiles = [Image.fromarray(vF).resize((sz, sz), Image.LANCZOS),
         Image.fromarray(np.dstack([v304, (v304 * 0.55).astype(np.uint8), (v304 * 0.25).astype(np.uint8)])).resize((sz, sz), Image.LANCZOS),
         Image.fromarray(rgbE).resize((sz, sz), Image.LANCZOS)]
full = Image.new('RGB', (3 * sz + 40, sz), (0, 0, 0))
for i, t in enumerate(tiles): full.paste(t, (i * (sz + 20), 0))
full.save(VISTES / 'c1_final_aia304_aia211-193-171_mateix_marc.jpg', quality=92)

# ---------------- desplegats polars (PA 0–360°, r 0,98–1,30)
NPA, NR = 3600, 320
pa = np.linspace(0, 360, NPA, endpoint=False); rr = np.linspace(0.98, 1.30, NR)
RR, PP = np.meshgrid(rr, pa, indexing='ij')
def desplega(img2d, g): return mostreja(img2d, g, RR, PP)
dF = {c: desplega(v, gcrop) for c, v in [('L', Lf), ('rosat', rosat), ('R', Rf), ('G', Gf), ('B', Bf)]}
dL = desplega(dins_lluna.astype(np.float32), gcrop) > 0.5
dA = {k: desplega(v[0], gcrop) for k, v in aia.items()}
np.savez_compressed(RES / 'C1_desplegats.npz', pa=pa, r=rr, lluna=dL, **{f'final_{k}': v for k, v in dF.items()},
                    **{f'aia_{k[0]}_{k[1]}': v for k, v in dA.items()})

# ---------------- encaix per correlació del senyal de protuberància (fora de la Lluna, r 1,00–1,12)
def treu_fons(a, s=(9, 61)):
    b = nd.median_filter(np.nan_to_num(a), size=s); return a - b
banda = (rr >= 1.0) & (rr <= 1.12)
def encaix(gC):
    """Desplaça el centre del Sol de la final per (dx, dy) i mesura la correlació 304 ↔ rosat."""
    A = treu_fons(dA[('0304', '1828')])
    out = []
    for dy in np.arange(-8, 8.01, 0.5):
        row = []
        for dx in np.arange(-8, 8.01, 0.5):
            g2 = Geo('t', gC.cx + dx, gC.cy + dy, gC.R, gC.n, gC.e, '', '')
            Fr = treu_fons(mostreja(rosat, g2, RR, PP)); Lm = mostreja(dins_lluna.astype(np.float32), g2, RR, PP) > 0.5
            m = banda[:, None] & ~Lm & np.isfinite(A) & np.isfinite(Fr)
            a, b = A[m], Fr[m]; a = (a - a.mean()) / a.std(); b = (b - b.mean()) / b.std()
            row.append(float(np.mean(a * b)))
        out.append(row)
    C = np.array(out); iy, ix = np.unravel_index(np.argmax(C), C.shape)
    sh = np.arange(-8, 8.01, 0.5)
    return C, sh[ix], sh[iy], C.max(), C[16, 16]
C, dx, dy, cmax, c0 = encaix(gcrop)
print(f"encaix 304↔rosat (centre efemèride): millor Δ = ({dx:+.1f}, {dy:+.1f}) px = ({dx*GEO['arcsec_px']:+.1f}″, {dy*GEO['arcsec_px']:+.1f}″); ρ {cmax:.3f} (a Δ=0: {c0:.3f})")
gcropS = Geo('final retall S', gS.cx - x0, gS.cy - y0, gS.R, gS.n, gS.e, '', '')
CS, dxS, dyS, cmaxS, c0S = encaix(gcropS)
print(f"encaix 304↔rosat (centre estrelles): millor Δ = ({dxS:+.1f}, {dyS:+.1f}) px; ρ {cmaxS:.3f} (a Δ=0: {c0S:.3f})")
json.dump(dict(centre_efemeride=[gF.cx, gF.cy], centre_estrelles=[gS.cx, gS.cy], arcsec_px=GEO['arcsec_px'],
               encaix_efemeride=dict(dx=dx, dy=dy, rho=cmax, rho_0=c0), encaix_estrelles=dict(dx=dxS, dy=dyS, rho=cmaxS, rho_0=c0S),
               retall=dict(x0=x0, y0=y0, M=M), aia_t_obs={f'{k[0]}_{k[1]}': v[1].data for k, v in aia.items()}),
          open(RES / 'C1_ENCAIX_304.json', 'w'), indent=1)
np.save(RES / 'C1_mapa_correlacio_efemeride.npy', C)
print('fet')

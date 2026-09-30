"""v4 (V120, 29-09-2026) · Vistes per a Pere, sempre al LLENÇ SENCER (els detalls, a més, mai en lloc seu). Adaptat de v119/v3.
  V120_V119_llenc_sencer.png      la V119 i la V120 (renders natius), sRGB, 1/4 cadascuna
  V120_canvi_sobre_V119.png       el que canvia: V120/V119 − 1 (lluminància, σ 1 px a 1/4), ±2 %
  V120_camp_desplacament.png      el camp que porta la Sony a la geometria de la Vixen (|u| en px, fletxes ×40)
  V120_registre_sony_vixen.png    DETALL: el detall fi de la Sony A (vermell) damunt del de la Vixen (cian), ABANS i DESPRÉS; gris = coincideixen
  V120_estrella_S20.png           DETALL: l'estrella de les 6 (S20, 2,15 R☉): la V119 i la V120, i la trama de totes dues (±1 %)
  V120_corona_interior.png        DETALL: la corona interior (±3,2 R☉), V119 i V120 amb el mateix estirament, a 1/2
  V120_vores.png                  DETALL: la vora de dalt del llenç i la cantonada de la B amb el camp de la Vixen (on la primera tirada fallava)
Ús: v4_vistes_V120.py <render_V120.tif> <carpeta_vistes>"""
import sys, json, importlib.util, numpy as np, tifffile, cv2
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ARREL = Path(__file__).resolve().parents[3]; O9 = ARREL / '4-RESULTATS/v119_20260929'; O0 = ARREL / '4-RESULTATS/v120_20260929'
T120, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
U119 = tifffile.memmap(O9 / 'V119_natiu/visible_complet.tif', mode='r'); U120 = tifffile.memmap(T120, mode='r'); H, W = U119.shape[:2]
SOL = (5361.768, 3775.748); RS = 440.603
MA = np.array([[0.5767309, 0.1855540, 0.1881852], [0.2973769, 0.6273491, 0.0752741], [0.0270343, 0.0706872, 0.9911085]])
MS = np.linalg.inv(np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])); TM = MS @ MA
def srgb(u16):
    lin = (np.asarray(u16, np.float32) / 65535) ** 2.19921875; s = np.clip(lin @ TM.T, 0, 1)
    return ((np.where(s <= 0.0031308, 12.92 * s, 1.055 * s ** (1 / 2.4) - 0.055)) * 255 + 0.5).astype(np.uint8)
def redueix(x, f): return x[:x.shape[0] // f * f, :x.shape[1] // f * f].reshape(x.shape[0] // f, f, x.shape[1] // f, f, *x.shape[2:]).mean((1, 3))
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 40); FP = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 26)
except Exception: F = FP = ImageFont.load_default()
def titol(img, t, font=None):
    im = Image.fromarray(img); ImageDraw.Draw(im).text((20, 16), t, fill=(255, 255, 255), font=font or F, stroke_width=3, stroke_fill=(0, 0, 0)); return np.asarray(im)
def mapa_div(r, exc, fons):
    x = np.clip(r / exc, -1, 1); c = (np.stack([np.where(x > 0, 1, 1 + x), 1 - np.abs(x), np.where(x < 0, 1, 1 - x)], 2) * 255).astype(np.uint8); c[fons] = 40; return c
def junta(a, b, sep=12): return np.concatenate([a, np.full((a.shape[0], sep, 3), 255, np.uint8), b], 1)
rep = {}
# 1-2 · llenç sencer i canvi
A4 = redueix(np.asarray(U119, np.float32), 4); B4 = redueix(np.asarray(U120, np.float32), 4)
Image.fromarray(junta(titol(srgb(A4), 'V119'), titol(srgb(B4), 'V120: la Sony a la geometria de la Vixen'))).save(OUT / 'V120_V119_llenc_sencer.png')
LA = ndi.gaussian_filter(np.asarray(U119, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]; LB = ndi.gaussian_filter(np.asarray(U120, np.float32).mean(2) / 65535, 1)[:H // 4 * 4:4, :W // 4 * 4:4]
r = np.where(LA > 0.004, LB / np.maximum(LA, 1e-6) - 1, 0); k = LA > 0.004
Image.fromarray(titol(mapa_div(r, 0.02, LA <= 0.004), 'V120 / V119 − 1, ±2 % (vermell = més clar a la V120)')).save(OUT / 'V120_canvi_sobre_V119.png')
rep['canvi_V120_sobre_V119_pct'] = {f'p{q}': round(float(np.percentile(r[k], q) * 100), 3) for q in (0.1, 1, 50, 99, 99.9)}
# 3 · el camp
spec = importlib.util.spec_from_file_location('camp_v120', Path(__file__).with_name('camp_v120.py')); cv = importlib.util.module_from_spec(spec); spec.loader.exec_module(cv)
MODEL = json.load(open(O0 / 'f1/CAMP_V120.json')); FA = np.load(ARREL / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_fA_v42.npy', mmap_mode='r')
st = 32; yy, xx = np.mgrid[0:H:st, 0:W:st].astype(np.float64); f = np.clip(np.asarray(FA[::st, ::st], np.float64), 0, 1)
ua = cv.camp(MODEL, 'A', xx, yy); ub = cv.camp(MODEL, 'B', xx, yy); ux = f * ua[0] + (1 - f) * ub[0]; uy = f * ua[1] + (1 - f) * ub[1]; mag = np.hypot(ux, uy)
rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
fig, ax = plt.subplots(figsize=(16, 11.4), dpi=110); im = ax.imshow(mag, extent=(0, W, H, 0), cmap='magma', vmin=0, vmax=np.percentile(mag, 99.5))
s2 = 12; ax.quiver(xx[::s2, ::s2], yy[::s2, ::s2], ux[::s2, ::s2], uy[::s2, ::s2], color='cyan', angles='xy', scale_units='xy', scale=1 / 40, width=0.0015)
for rs_, ls in ((1.0, '-'), (2.0, '--'), (4.0, ':'), (6.0, ':')):
    ax.add_patch(plt.Circle(SOL, rs_ * RS, fill=False, color='white', ls=ls, lw=1))
ax.text(SOL[0] + 2.05 * RS, SOL[1], '2 R☉: fins aquí, només la Vixen', color='white', fontsize=11)
plt.colorbar(im, ax=ax, fraction=0.03, label='desplaçament de la Sony (px)')
ax.set_title('El camp que porta la Sony (A i B, amb la seva barreja) a la geometria de la Vixen · fletxes ×40', fontsize=14); ax.set_xlim(0, W); ax.set_ylim(H, 0)
fig.tight_layout(); fig.savefig(OUT / 'V120_camp_desplacament.png'); plt.close(fig)
rep['camp_px'] = {f'{a}-{b} R☉': [round(float(np.median(mag[(rr >= a) & (rr < b)])), 2), round(float(mag[(rr >= a) & (rr < b)].max()), 2)] for a, b in ((1, 2), (2, 3), (3, 4.5), (4.5, 6), (6, 9))}
# 4 · el registre Sony–Vixen, abans i després: una finestra a 3 R☉ on el camp és més gran
X0, Y0 = 4250 - 300, 4450 - 200; ys, xs = slice(Y0, Y0 + 400), slice(X0, X0 + 600); r_fin = float(np.hypot(4250 - SOL[0], 4450 - SOL[1]) / RS)
m_ = [float(np.hypot(*cv.camp(MODEL, 'A', np.array([4250.]), np.array([4450.])))[0])]; i = 0
def det(path):
    a = np.load(path, mmap_mode='r'); L = np.asarray(a[ys, xs], np.float32); L = (L[..., 0] + 2 * L[..., 1] + L[..., 2]) / 4 if L.ndim == 3 else L
    l = np.log(np.maximum(L, 1e-6)); d = cv2.GaussianBlur(l, (0, 0), 1.5) - cv2.GaussianBlur(l, (0, 0), 8); return d / (np.percentile(np.abs(d), 99) + 1e-9)
DV = det(ARREL / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/vixen_total.npy')
Dold = det(ARREL / '4-RESULTATS/v112_claude_20260928/fonts_v113_vora/apilats/sony_A_total.npy'); Dnew = det(O0 / 'sony_v/sony_A_total_v113vora.npy')
def anag(ds, dv):
    s = np.clip(0.5 + 0.5 * ds, 0, 1); v = np.clip(0.5 + 0.5 * dv, 0, 1); return (np.stack([s, v, v], 2) * 255).astype(np.uint8)
g = lambda x: cv2.resize(x, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_NEAREST)
Image.fromarray(junta(titol(g(anag(Dold, DV)), f'ABANS · Sony A (vermell) sobre Vixen (cian) · {r_fin:.1f} Rsol', FP),
                      titol(g(anag(Dnew, DV)), 'DESPRÉS (V120) · gris = coincideixen', FP))).save(OUT / 'V120_registre_sony_vixen.png')
rep['finestra_registre'] = [X0, Y0, X0 + 600, Y0 + 400]; rep['finestra_registre_camp_A_px'] = round(float(m_[i]), 2)
rep['correlacio_detall_Sony_A_Vixen'] = dict(abans=round(float(np.corrcoef(Dold.ravel(), DV.ravel())[0, 1]), 3), despres=round(float(np.corrcoef(Dnew.ravel(), DV.ravel())[0, 1]), 3))
# 5 · l'estrella de les 6 (S20)
C = json.load(open(O0 / 'estrelles/CATALEG_ACCEPTAT_V120.json')); s20 = next(s for s in C['stars'] if s['id'] == 'S20')
xc, yc = int(round(s20['x'])), int(round(s20['y'])); hw = 140; ys, xs = slice(yc - hw, yc + hw), slice(xc - hw, xc + hw)
c9, c0 = [np.asarray(U[ys, xs], np.float32) for U in (U119, U120)]; s9, s0 = srgb(c9), srgb(c0); lo, hi = np.percentile(np.concatenate([s9.ravel(), s0.ravel()]), [1, 99.5])
st_ = lambda q: np.clip((q.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
t9 = np.asarray(np.load(O9 / 'trama/capa_trama/L415_G.npy', mmap_mode='r')[ys, xs], np.float32) / 65535 - 0.5
t0 = np.asarray(np.load(O0 / 'ot/trama/capa/L415_G.npy', mmap_mode='r')[ys, xs], np.float32) / 65535 - 0.5
z = lambda x: cv2.resize(x, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
fila1 = junta(titol(z(st_(s9)), 'V119 · S20 (6 h, 2,15 Rsol)', FP), titol(z(st_(s0)), 'V120', FP))
fila2 = junta(titol(z(mapa_div(t9, 0.01, np.zeros_like(t9, bool))), 'trama V119 (u − ½, ±1 %): el disc neutre', FP), titol(z(mapa_div(t0, 0.01, np.zeros_like(t0, bool))), 'trama V120: el nivell del voltant', FP))
Image.fromarray(np.concatenate([fila1, np.full((12, fila1.shape[1], 3), 255, np.uint8), fila2], 0)).save(OUT / 'V120_estrella_S20.png')
rr_ = np.hypot(*np.mgrid[-hw:hw, -hw:hw]); anell = (rr_ > 20) & (rr_ < 45); fora = (rr_ > 60) & (rr_ < 120)
def clot(c_): L = c_.mean(2); return round(float(L[anell].mean() / L[fora].mean() - 1) * 100, 2)
rep['S20'] = dict(pos=[xc, yc], trama_dins_20px=dict(V119=round(float(t9[rr_ < 20].mean() * 100), 3), V120=round(float(t0[rr_ < 20].mean() * 100), 3)),
                  trama_voltant_60_120px=dict(V119=round(float(t9[fora].mean() * 100), 3), V120=round(float(t0[fora].mean() * 100), 3)),
                  anell_20_45_sobre_voltant_pct=dict(V119=clot(c9), V120=clot(c0)))
# 6 · la corona interior
hw, hh = int(3.2 * RS), int(2.4 * RS); ys, xs = slice(int(SOL[1] - hh), int(SOL[1] + hh)), slice(int(SOL[0] - hw), int(SOL[0] + hw))
cr = [srgb(redueix(np.asarray(U[ys, xs], np.float32), 2)) for U in (U119, U120)]; lo, hi = np.percentile(np.concatenate([c_.ravel() for c_ in cr]), [1, 99.7])
fil = [titol(np.clip((c_.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8), f'{n} · corona interior a 1/2, mateix estirament', FP) for n, c_ in zip(('V119', 'V120'), cr)]
Image.fromarray(junta(fil[0], fil[1], 10)).save(OUT / 'V120_corona_interior.png')
rep['finestra_corona_interior'] = [xs.start, ys.start, xs.stop, ys.stop]
# 7 · les vores (lliçó de la primera tirada): la vora de dalt del llenç i la cantonada de la B amb el camp de la Vixen (9,3 Rsol)
def talls(cx, cy, hw, hh):
    ys, xs = slice(max(0, cy - hh), cy + hh), slice(max(0, cx - hw), cx + hw); a = np.asarray(U119[ys, xs], np.float32).mean(2); b = np.asarray(U120[ys, xs], np.float32).mean(2)
    lo, hi = np.percentile(np.concatenate([a.ravel(), b.ravel()]), [1, 99.5]); q = lambda x: np.repeat((np.clip((x - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)[..., None], 3, 2)
    return q(a), q(b), a, b
fil = []
for nom, (cx, cy, hw, hh) in (('vora de dalt', (6000, 60, 400, 60)), ('cantonada B · Vixen', (9080, 5465, 250, 200))):
    qa, qb, a, b = talls(cx, cy, hw, hh); rep[f'vora_{nom}'] = dict(mitjana_V119=round(float(a.mean()), 1), mitjana_V120=round(float(b.mean()), 1), max_dif_pct_fila_o_disc=round(float(np.abs(b.mean(1) / np.maximum(a.mean(1), 1) - 1).max() * 100), 2))
    fil.append(junta(titol(qa, f'V119 · {nom}', FP), titol(qb, f'V120 · {nom}', FP)))
w_ = max(f.shape[1] for f in fil); fil = [np.pad(f, ((0, 12), (0, w_ - f.shape[1]), (0, 0)), constant_values=255) for f in fil]
Image.fromarray(np.concatenate(fil, 0)).save(OUT / 'V120_vores.png')
(OUT / 'V4_VISTES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False))

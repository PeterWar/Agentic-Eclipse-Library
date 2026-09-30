"""v1 · Vistes per a Pere (ronda 2, sony_A):
  VISTA_1_llenc_sencer_A_B_AmenysB.png: LLENÇ SENCER (1/5) del detall fi (residu relatiu σ 3/40 px, ±0,12 %) de l'apilat A, de l'apilat B,
     de A − B i de (A + B)/2, tots amb el flat 2D del pilot; T1 i T2 marcats amb dues rectes paral·leles a ±40 px (el traç queda al mig,
     sense tapar); en verd, la vora del camp de B.
  GRAFIC_perfils_T1_T2.png: perfils perpendiculars (mitjana al llarg del traç, respecte dels flancs 12–60 px) de T1 als apilats i a les
     meitats temporals, i de T2 a les variants del flat.
Només llegeix; escriu a 4-RESULTATS/v108_20260926/sony_A/."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
P = 5; LIM = 0.0012
a, ca = obre('A_f2d'); b, cb = obre('B_f2d')
def rel_sencer(arr, ch):
    out = np.full((H, W), np.nan, np.float32)
    for y0 in range(0, H, 1800):
        ya, yb = max(0, y0 - 200), min(H, y0 + 2000); img = retall(arr, ch, (0, ya, W, yb)); r = rel_map(img, 40.0, 3.0, 41)
        out[y0:min(H, y0 + 1800)] = r[y0 - ya:y0 - ya + min(1800, H - y0)]
    return out
rA = rel_sencer(a, ca); rB = rel_sencer(b, cb)
pans = {'A (apuntament A, flat 2D del pilot)': rA, 'B (apuntament B, flat 2D del pilot)': rB, 'A - B (on hi ha tots dos)': rA - rB, '(A + B) / 2 (on hi ha tots dos)': 0.5 * (rA + rB)}
Bw = np.isfinite(rB)
tiles = []
for tit, r in pans.items():
    ok = np.isfinite(r).astype(np.float32); v = np.nan_to_num(r)
    sm = cv2.resize(v * ok, (W // P, H // P), interpolation=cv2.INTER_AREA) / np.maximum(cv2.resize(ok, (W // P, H // P), interpolation=cv2.INTER_AREA), 1e-6)
    okp = cv2.resize(ok, (W // P, H // P), interpolation=cv2.INTER_AREA) > 0.5
    u8 = np.where(okp, np.clip(128 + 127 * sm / LIM, 0, 255), 40).astype(np.uint8); rgb = cv2.cvtColor(u8, cv2.COLOR_GRAY2BGR)
    cnt, _ = cv2.findContours((cv2.resize(Bw.astype(np.uint8), (W // P, H // P), interpolation=cv2.INTER_NEAREST)).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(rgb, cnt, -1, (60, 170, 60), 1)
    for k, tr in TRACOS.items():
        col = (214, 120, 42) if k == 1 else (40, 110, 235)   # BGR: T1 blau, T2 taronja
        for sg in (-40, 40):
            p0 = (tr['extrems'][0] + sg * tr['n']) / P; p1 = (tr['extrems'][1] + sg * tr['n']) / P
            cv2.line(rgb, tuple(np.round(p0).astype(int)), tuple(np.round(p1).astype(int)), col, 1, cv2.LINE_AA)
        q = (tr['extrems'][0] + 70 * tr['n']) / P; cv2.putText(rgb, f'T{k}', tuple(np.round(q).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)
    cv2.circle(rgb, (int(SOL[0] / P), int(SOL[1] / P)), int(RSOL / P), (0, 200, 255), 1)
    cap = np.full((44, rgb.shape[1], 3), 252, np.uint8); cv2.putText(cap, tit, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (11, 11, 11), 2)
    tiles.append(np.vstack([cap, rgb]))
fila1 = np.hstack([tiles[0], np.full((tiles[0].shape[0], 8, 3), 252, np.uint8), tiles[1]]); fila2 = np.hstack([tiles[2], np.full((tiles[2].shape[0], 8, 3), 252, np.uint8), tiles[3]])
img = np.vstack([fila1, np.full((8, fila1.shape[1], 3), 252, np.uint8), fila2])
peu = np.full((70, img.shape[1], 3), 252, np.uint8)
cv2.putText(peu, 'Llenc sencer a 1/5. Detall fi: residu relatiu sigma 3/40 px, escala +-0,12 % (negre = mes fosc). T1 (blau) i T2 (taronja): el traç va entre les dues rectes (+-40 px).', (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (11, 11, 11), 1)
cv2.putText(peu, 'Verd: vora del camp de B. Gris fosc: sense dada. A - B treu el cel (el mateix a tots dos); hi queda el que es propi de cada sensor (a 749 px l un de l altre).', (10, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (11, 11, 11), 1)
cv2.imwrite(str(OUT / 'VISTA_1_llenc_sencer_A_B_AmenysB.png'), np.vstack([img, peu]))
print('vista 1 feta', img.shape, flush=True)
del rA, rB, pans
# ---------- gràfic de perfils ----------
S1 = np.load(OUT / 'S1_perfils.npz'); t1 = S1['t']
def norm(t, pr): f = (np.abs(t) >= 12) & (np.abs(t) <= 60); return (pr - np.nanmean(pr[f])) * 1e4
def suau(y, s=3):   # s mostres de 0,5 px → σ 1,5 px
    k = np.exp(-0.5 * (np.arange(-4 * s, 4 * s + 1) / s) ** 2); k /= k.sum(); yy = np.nan_to_num(y); w = np.isfinite(y).astype(float)
    return np.convolve(yy, k, 'same') / np.maximum(np.convolve(w, k, 'same'), 1e-6)
tr = TRACOS[1]; box = caixa_tr(tr, 700); prs = {}
for nom in ('A_f2d', 'B_f2d'):
    arr, ch = obre(nom); t, pr, _ = perfil(rel_map(retall(arr, ch, box)), box[:2], tr['centre'], tr['d'], tr['llarg']); prs[nom] = norm(t, pr)
prs['A-B'] = prs['A_f2d'] - prs['B_f2d']; prs['(A+B)/2'] = 0.5 * (prs['A_f2d'] + prs['B_f2d']); tT1 = t
MEI = {}
for mn in ('A1', 'A2', 'B1', 'B2'):
    z = np.load(OUT / f'meitats_flat2d/{mn}.npz'); x0, y0, x1, y1 = box; img = z['G'][y0:y1, x0:x1] if y1 <= 4200 else None; w = z['w'][y0:y1, x0:x1]
    img = np.where(np.isfinite(img) & (w > 0.05 * np.nanmax(w)), img, 0).astype(np.float32); t, pr, _ = perfil(rel_map(img), (x0, y0), tr['centre'], tr['d'], tr['llarg']); MEI[mn] = norm(t, pr)
VAR2 = {}
for nom, p in (('control (flat radial)', CR / 'b2_sony_A/cau/sony_A_total_v36.npy'), ('flat 2D del pilot', PIL / 'flat2d/sony_A_total.npy'), ('flat 2D Wiener', OUT / 'variant_wiener/apilats/sony_A_total.npy'), ('Wiener desplaçat (nul)', OUT / 'variant_wiener_nul/apilats/sony_A_total.npy')):
    tr2 = TRACOS[2]; b2 = caixa_tr(tr2, 700); arr = np.load(p, mmap_mode='r'); t, pr, _ = perfil(rel_map(retall(arr, 1, b2)), b2[:2], tr2['centre'], tr2['d'], tr2['llarg']); VAR2[nom] = norm(t, pr)
COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']; SUP = '#fcfcfb'; TX = '#0b0b0b'; TX2 = '#52514e'
plt.rcParams.update({'font.size': 11, 'axes.edgecolor': TX2, 'axes.labelcolor': TX, 'xtick.color': TX2, 'ytick.color': TX2, 'text.color': TX})
fig, axs = plt.subplots(1, 3, figsize=(18, 5.6), facecolor=SUP)
def dibuixa(ax, t, dades, titol):
    ax.set_facecolor(SUP); k = np.abs(t) <= 40
    for (nom, y), c in zip(dades.items(), COL):
        ys = suau(y); ax.plot(t[k], ys[k], color=c, lw=2, label=nom)
    ax.axhline(0, color='#c9c8c3', lw=1); ax.axvline(0, color='#c9c8c3', lw=1, ls=':')
    ax.set_xlabel('distància perpendicular al traç (px del llenç)'); ax.set_title(titol, fontsize=12, loc='left'); ax.grid(axis='y', color='#ecebe7', lw=0.8)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=10, loc='lower left')
dibuixa(axs[0], tT1, {'A': prs['A_f2d'], 'B': prs['B_f2d'], 'A − B': prs['A-B'], '(A + B)/2': prs['(A+B)/2']}, 'T1 als apilats (flat 2D del pilot)')
axs[0].set_ylabel('residu respecte dels flancs (‱)')
dibuixa(axs[1], tT1, {'A1 (t ≤ 18 s)': MEI['A1'], 'A2 (t ≥ 28 s)': MEI['A2'], 'B1 (t ≤ 70 s)': MEI['B1'], 'B2 (t ≥ 80 s)': MEI['B2']}, 'T1 a les meitats temporals (flat 2D del pilot)')
dibuixa(axs[2], tT1, VAR2, 'T2 a l\'apilat A, segons el flat')
fig.tight_layout(); fig.savefig(OUT / 'GRAFIC_perfils_T1_T2.png', dpi=110, facecolor=SUP); print('gràfic fet', flush=True)

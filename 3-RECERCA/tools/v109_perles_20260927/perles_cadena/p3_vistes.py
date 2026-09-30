"""p3 (V109 · perles a la cadena) · Vistes per a l'INFORME (norma de Pere: el llenç SENCER; el detall, a més, mai en lloc seu).
  VISTA_1_llenc_sencer_canvi.png   el llenç sencer (pas 2): dalt, ln(V108/V107) del compost FUSIONAT (el que desa el Photoshop); a sota, el
                                   de la pila ràster sense capes d'ajust (PLE, emulada). Escala ±2 %, blau = baixa, vermell = puja, gris = 0.
                                   L'arc groc marca la zona de les perles (PA 155–190°, 0–80 px del limbe).
  VISTA_2_detall_perles.png        detall a més (1:1 × 4) de la zona de les perles: fusionat V107 | fusionat V108 | Δ fusionat | Δ PLE | Δ C1 (±2 %).
  VISTA_3_perfils_perles.png       perfil al llarg del limbe (PA 150–200°, màxim a d 0–6 px): el fusionat V107 i V108, i Δ ln a cada etapa.
  VISTA_4_beta_per_etapa.png       β (DoG σ1–4: la part del detall del control que la v108 conserva, − = pèrdua) per etapa i banda, perles i resta.
Només lectura; escriu a 4-RESULTATS/v109_perles_20260927/perles_cadena/vistes/."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_perles import OUT, V8, CTL, V108, PSB7, PSB8, LLUNA, RLLUNA, W, H, fusionat, lum, _pos_image_data  # noqa: E402
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
VI = OUT / 'vistes'; VI.mkdir(parents=True, exist_ok=True); CO = V8 / 'v108_final/composts'
BLAU, GRIS, VERM = '#2a78d6', '#f0efec', '#e34948'
CMAP = LinearSegmentedColormap.from_list('div', [BLAU, GRIS, VERM])
LUT = (np.array([CMAP(i / 255)[:3] for i in range(256)])[:, ::-1] * 255 + 0.5).astype(np.uint8)   # BGR per a cv2


def colora(d, lim=0.02):
    i = np.clip((np.nan_to_num(d) / lim + 1) / 2 * 255, 0, 255).astype(np.uint8); return LUT[i]


def arc(img, pas, color=(0, 215, 255)):
    for rr in (RLLUNA, RLLUNA + 80):
        t = np.radians(np.arange(155, 190.01, 0.05)); pts = np.stack([(LLUNA[0] + np.cos(t) * rr) / pas, (LLUNA[1] - np.sin(t) * rr) / pas], 1)
        cv2.polylines(img, [np.round(pts * 16).astype(np.int32)], False, color, 2, cv2.LINE_AA, shift=4)


# ------------------------------------------------------------------ VISTA 1: llenç sencer, pas 2
PAS = 2


def fus2(p):
    pos, nch, h, w = _pos_image_data(p); mm = np.memmap(p, dtype='>u2', mode='r', offset=pos, shape=(nch, h, w))
    return lum(np.stack([np.asarray(mm[c, ::PAS, ::PAS], np.float32) / 65535 for c in range(3)], -1))


dF = np.log(np.maximum(fus2(PSB8), 1e-4)) - np.log(np.maximum(fus2(PSB7), 1e-4))
q7 = np.asarray(np.load(CO / 'L_V107.npy', mmap_mode='r')[::PAS, ::PAS], np.float32); q8 = np.asarray(np.load(CO / 'L_V108.npy', mmap_mode='r')[::PAS, ::PAS], np.float32)
dP = np.where((q7 > 1e-5) & (q8 > 1e-5), np.log(np.maximum(q8, 1e-6)) - np.log(np.maximum(q7, 1e-6)), 0)
panells = []
for d, txt in ((dF, 'FUSIONAT (Photoshop, amb capes d\'ajust): ln(V108/V107), escala +-2 %'), (dP, 'PLE (pila raster sense ajust, emulada): ln(V108/V107), escala +-2 %')):
    im = colora(d).copy(); arc(im, PAS)
    cv2.putText(im, txt, (40, 90), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (20, 20, 20), 5, cv2.LINE_AA); panells.append(im)
cv2.imwrite(str(VI / 'VISTA_1_llenc_sencer_canvi.png'), np.concatenate([panells[0], np.full((20, panells[0].shape[1], 3), 255, np.uint8), panells[1]], 0))
del dF, dP, q7, q8, panells
print('VISTA_1', flush=True)

# ------------------------------------------------------------------ VISTA 2: detall (a més), 1:1 × 4
BX = (4860, 3560, 5000, 3880); x0, y0, x1, y1 = BX; E = 4
A = fusionat(PSB7, BX); B = fusionat(PSB8, BX)
c1a = np.asarray(np.load(CO / 'C1_V107.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32); c1b = np.asarray(np.load(CO / 'C1_V108.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32)
pa = np.asarray(np.load(CO / 'L_V107.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32); pb = np.asarray(np.load(CO / 'L_V108.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32)
lnq = lambda b, a: np.log(np.maximum(b, 1e-6)) - np.log(np.maximum(a, 1e-6))
cols = [(np.clip(A, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8), (np.clip(B, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8),
        colora(lnq(lum(B), lum(A))), colora(lnq(pb, pa)), colora(lnq(c1b, c1a))]
tit = ['fusionat V107', 'fusionat V108', 'D fusionat', 'D PLE (sense ajust)', 'D C1 (base+filtres)']
out = []
for im, t in zip(cols, tit):
    im = cv2.resize(im, None, fx=E, fy=E, interpolation=cv2.INTER_NEAREST)
    cv2.putText(im, t, (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 3, cv2.LINE_AA); cv2.putText(im, t, (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 1, cv2.LINE_AA)
    out.append(im); out.append(np.full((im.shape[0], 8, 3), 255, np.uint8))
cv2.imwrite(str(VI / 'VISTA_2_detall_perles.png'), np.concatenate(out[:-1], 1))
print('VISTA_2', flush=True)

# ------------------------------------------------------------------ VISTA 3: perfils al llarg del limbe
BX = (4677, 3077, 6077, 4477); x0, y0, x1, y1 = BX
th = np.radians(np.arange(150, 200, 0.02)); dd = np.arange(0, 6.01, 0.25)
XP = (LLUNA[0] - x0 + np.cos(th)[None, :] * (RLLUNA + dd[:, None])).astype(np.float32); YP = (LLUNA[1] - y0 - np.sin(th)[None, :] * (RLLUNA + dd[:, None])).astype(np.float32)
def perfil(img): return cv2.remap(np.ascontiguousarray(img, np.float32), XP, YP, cv2.INTER_LINEAR).max(0)
def crop(p, c=None):
    a = np.load(p, mmap_mode='r')[y0:y1, x0:x1]; return np.asarray(a if c is None else a[..., c], np.float32)
S = {'linealitzada (base_G)': (crop(CTL / 'lineal/base_G.npy'), crop(V108 / 'lineal/base_G.npy')),
     'base, capa 3 (G)': (crop(CTL / 'estat_v108/L3_RGB.npy', 1), crop(V108 / 'estat_v108/L3_RGB.npy', 1)),
     'C1 (base + filtres)': (crop(CO / 'C1_V107.npy'), crop(CO / 'C1_V108.npy')),
     'PLE (+ capes de Pere)': (crop(CO / 'L_V107.npy'), crop(CO / 'L_V108.npy')),
     'fusionat (+ capes d\'ajust)': (lum(fusionat(PSB7, BX)), lum(fusionat(PSB8, BX)))}
paa = np.degrees(th); prof = {}
fig, ax = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True, gridspec_kw=dict(height_ratios=[1.1, 1]))
f7, f8 = perfil(S['fusionat (+ capes d\'ajust)'][0]), perfil(S['fusionat (+ capes d\'ajust)'][1])
ax[0].plot(paa, f7, color='#2a78d6', lw=2, label='V107'); ax[0].plot(paa, f8, color='#eb6834', lw=1.2, label='V108')
ax[0].set_ylabel('fusionat, L (màxim a 0–6 px del limbe)'); ax[0].legend(frameon=False, loc='lower left')
ax[0].set_title('Perles de Baily al llarg del limbe esquerre: el perfil del compost que desa el Photoshop', loc='left', fontsize=11)
cols = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']
for (nom, (a, b)), c in zip(S.items(), cols):
    pa_, pb_ = perfil(a), perfil(b); d = 100 * (np.log(np.maximum(pb_, 1e-9)) - np.log(np.maximum(pa_, 1e-9)))
    prof[nom] = dict(dln_pc_mediana=round(float(np.median(d)), 4), dln_pc_rms=round(float(np.sqrt(np.mean(d ** 2))), 4), dln_pc_min=round(float(d.min()), 4), dln_pc_max=round(float(d.max()), 4))
    ax[1].plot(paa, d, color=c, lw=2 if nom.startswith('fus') else 1.5, label=nom)
ax[1].axhline(0, color='#52514e', lw=0.6); ax[1].set_ylabel('ln(V108/V107) al perfil (%)'); ax[1].set_xlabel('angle de posició al voltant de la Lluna (°; 180° = les 9 h)')
ax[1].legend(frameon=False, ncol=3, fontsize=9, loc='upper left')
for a in ax:
    a.spines[['top', 'right']].set_visible(False); a.grid(axis='y', color='#e5e4e0', lw=0.6); a.axvspan(155, 190, color='#f0efec', zorder=0)
plt.tight_layout(); plt.savefig(VI / 'VISTA_3_perfils_perles.png', dpi=110); plt.close()
print('VISTA_3', prof, flush=True)

# ------------------------------------------------------------------ VISTA 4: β per etapa i banda
R = json.loads((OUT / 'P1_ETAPES.json').read_text())
files = ['LF_suma_G (Σnum, pes>0)', 'FONTS fusion_starless G', 'FRANJA a3d E', 'FRANJA total G (control → v108)', 'LINEAL fusion_starless', 'BASE base_v108_u16 G',
         'BASE base_v108_final_u16 G'] + [f'ESTAT L{i}_G' for i in (41, 42, 43, 45, 46, 47, 49, 51, 54, 55, 56)] + \
        ['COMPOST C1 (base + 10 filtres)', 'COMPOST PLE (+ capes de Pere, sense ajust)', 'COMPOST FUSIONAT (Photoshop, amb ajust)']
bandes = ['0..3', '3..6', '6..10', '10..20', '20..40', '40..80']
fig, axs = plt.subplots(1, 2, figsize=(14, 8.5), sharey=True)
for ax_, z in zip(axs, ('PERLES', 'RESTA')):
    M = np.full((len(files), len(bandes)), np.nan)
    for i, f in enumerate(files):
        v = R[f]
        for j, b in enumerate(bandes):
            M[i, j] = 0.0 if v.get('identic') else (v[z].get(b, {}).get('1-4', {}).get('beta', np.nan) if z in v else np.nan)
    ax_.imshow(M, cmap=CMAP.reversed(), vmin=-0.06, vmax=0.06, aspect='auto')
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isfinite(M[i, j]): ax_.text(j, i, f'{M[i, j]:+.3f}', ha='center', va='center', fontsize=7.5, color='#0b0b0b')
    ax_.set_xticks(range(len(bandes))); ax_.set_xticklabels([b.replace('..', '–') + ' px' for b in bandes], fontsize=8)
    ax_.set_title('zona de les perles (PA 155–190°)' if z == 'PERLES' else 'resta del limbe', fontsize=10, loc='left')
axs[0].set_yticks(range(len(files))); axs[0].set_yticklabels([f.replace('COMPOST ', '').replace(' (Σnum, pes>0)', '') for f in files], fontsize=8)
fig.suptitle('β del detall σ1–4 px (Δ projectat sobre el detall de la V107): − = la V108 en perd, + = en guanya, 0 = el conserva', fontsize=11, x=0.02, ha='left')
plt.tight_layout(); plt.savefig(VI / 'VISTA_4_beta_per_etapa.png', dpi=110); plt.close()
(OUT / 'P3_PERFILS.json').write_text(json.dumps(prof, ensure_ascii=False, indent=1) + '\n')
print('fet')

"""v2_vistes_sensor_v3 (V108, flat2d_v3) · Vistes DEL SENSOR SENCER (subplà) de la C: què es treu i què es queda.
  S1 · Sony: ln C de la v2 R − G (banda 8–60 subplans, ±8 ‱) — els anells i les línies cromàtiques que la v3 treu; al costat, la v3 (comuna: zero
       de color) i el perfil radial dels anells al voltant del seu centre (2832, 4092) px RAW, amb el centre de la cadena (2660, 4000) marcat.
  S2 · Estructures de ℓ' (z multiescala) amb la decisió de la porta per grup: verd = s'aplica, vermell = no (sense prova), gris = fora del llenç.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v3/VISTA_S1_sony_color_de_C.png i VISTA_S2_porta_estructures.png   (només lectura; ~2 GB)"""
import json
from pathlib import Path
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F = OUT / 'flat2d'
V2 = A / '4-RESULTATS/v108_20260926/flat2d_v2/flat2d'
def lnsub(p):
    C = np.load(p)['C']; return {(oy, ox): np.log(C[oy::2, ox::2]) for oy in range(2) for ox in range(2)}
def banda(x, a, b): return cv2.GaussianBlur(x, (0, 0), a) - cv2.GaussianBlur(x, (0, 0), b)
# S1
L2 = lnsub(V2 / 'SONYTOT_flat2d_v2.npz'); L3 = lnsub(F / 'SONYTOT_A_flat2d_v3.npz')
rg2 = banda(L2[(0, 0)] - 0.5 * (L2[(0, 1)] + L2[(1, 0)]), 8, 60); rg3 = banda(L3[(0, 0)] - 0.5 * (L3[(0, 1)] + L3[(1, 0)]), 8, 60)
g2 = banda(0.25 * sum(L2.values()), 8, 60); g3 = banda(0.25 * sum(L3.values()), 8, 60)
fig, ax = plt.subplots(2, 3, figsize=(30, 14), gridspec_kw=dict(width_ratios=[1, 1, 0.8]))
for i, (x, t) in enumerate(((rg2, 'v2 · ln C, R − G, banda 8–60 subplans, ±8 ‱'), (rg3, 'v3 · ln C, R − G (comuna: 0)'))):
    ax[0, i].imshow(x[::2, ::2], cmap='bwr', vmin=-8e-4, vmax=8e-4); ax[0, i].set_title(t, fontsize=15); ax[0, i].axis('off')
for i, (x, t) in enumerate(((g2, 'v2 · ln C comuna (mitjana dels 4 canals), 8–60 subplans, ±8 ‱'), (g3, 'v3 · ln C comuna (sense anells; porta de l\'apuntament A)'))):
    ax[1, i].imshow(x[::2, ::2], cmap='bwr', vmin=-8e-4, vmax=8e-4); ax[1, i].set_title(t, fontsize=15); ax[1, i].axis('off')
for a_ in (ax[0, 0], ax[0, 1], ax[1, 0], ax[1, 1]):
    a_.plot([4092.5 / 4], [2832.5 / 4], 'k+', ms=18, mew=2); a_.plot([4000 / 4], [2660 / 4], 'gx', ms=14, mew=2)
p = np.load(F.parent / 'diag/components/SONYTOT_perfils_radials_ca.npz'); r = np.arange(len(p['L']))
for k, nm in (('K0', 'κ R'), ('K2', 'κ B'), ('L', 'ℓ comuna')): ax[0, 2].plot(r, 1e4 * p[k], lw=0.7, label=nm)
ax[0, 2].set_xlim(0, 2300); ax[0, 2].set_ylim(-12, 12); ax[0, 2].legend(); ax[0, 2].set_xlabel('radi al centre dels anells (subplans)'); ax[0, 2].set_ylabel('‱')
ax[0, 2].set_title('perfil per anells al voltant de (2832, 4092) px RAW (+ negra); × verda = centre de la cadena', fontsize=12)
DQ = json.loads((F.parent / 'diag/D2_PROVA_AB_anells.json').read_text())['quantitats']
bs = ['2-6px', '6-18px', '18-54px', '54-160px']; an = '6-10'
for c, col in (('Kr_ca', 'C3'), ('Kn_ca', 'C0'), ('Ln_ca', 'C2')):
    D = DQ['lnG' if c == 'Ln_ca' else 'lnRG']
    y = [D[b][an][c]['beta'] if D[b].get(an) and D[b][an][c]['beta'] is not None else np.nan for b in bs]; e = [D[b][an][c]['sigma_nul'] if D[b].get(an) and D[b][an][c]['sigma_nul'] is not None else np.nan for b in bs]
    ax[1, 2].errorbar(range(4), y, yerr=e, fmt='o-', color=col, label={'Kr_ca': 'anells cromàtics', 'Kn_ca': 'cromàtica no radial', 'Ln_ca': 'comuna no radial (ln G)'}[c], capsize=4)
ax[1, 2].axhline(-1, color='k', ls=':'); ax[1, 2].axhline(0, color='k', lw=0.5); ax[1, 2].set_xticks(range(4)); ax[1, 2].set_xticklabels(bs); ax[1, 2].set_ylim(-2.5, 1)
ax[1, 2].legend(); ax[1, 2].set_title('prova A − B de la Sony a 6–10 R☉ (cromàtiques a ln R/G; comuna a ln G): β = −1 hi és sencer, 0 no hi és', fontsize=12)
plt.tight_layout(); fig.savefig(OUT / 'VISTA_S1_sony_color_de_C.png', dpi=60); plt.close(fig); print('FET S1', flush=True)
# S2
fig, ax = plt.subplots(1, 3, figsize=(33, 8)); npan = 0
for i, (T, grups) in enumerate((('SONYTOT', ('sony_A', 'sony_B')), ('VIXEN', ('vixen',)))):
    Z = np.load(F / f'{T}_components_v3.npz'); zm = Z['zmax']; lab = Z['lab']; E = json.loads((F / f'ESTRUCTURES_{T}.json').read_text())['estructures']; P = json.loads((F / f'G1_PORTA_{T}.json').read_text())['grups']
    for j, g in enumerate(grups):
        a_ = ax[npan]; npan += 1; a_.imshow(zm[::2, ::2], cmap='bwr', vmin=-6, vmax=6); a_.set_title(f'{T} · z multiescala de ℓ\' · porta de {g}', fontsize=14); a_.axis('off')
        for e in E:
            d = P[g]['decisions'][str(e['id'])]; col = 'lime' if d.get('aplica') else ('0.5' if 'a' not in d else 'red')
            x0, y0, x1, y1 = e['caixa_subpla']; a_.add_patch(plt.Rectangle((x0 / 2, y0 / 2), max((x1 - x0) / 2, 3), max((y1 - y0) / 2, 3), fill=False, ec=col, lw=1.6))
            a_.text(x1 / 2 + 3, y0 / 2, str(e['id']) + (f" a={d['a']:.2f}" if 'a' in d else ''), color=col, fontsize=8)
plt.tight_layout(); fig.savefig(OUT / 'VISTA_S2_porta_estructures.png', dpi=60); plt.close(fig); print('FET S2', flush=True)

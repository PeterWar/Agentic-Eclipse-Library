"""s5 · Tres proves més per a T1 i T2, totes a la mateixa geometria fixa i amb nul a la mateixa imatge:
(a) A − B: el residu relatiu de l'apilat A menys el de l'apilat B (flat 2D) al llarg de T1. Si el traç fos del sensor d'A (i no del cel),
    A − B el mostraria sencer; si és del cel, A − B ≈ 0.
(b) COLOR del solc: profunditat relativa a R, G i B (espai de color de l'apilat). Un defecte de transmissió (flat, fil, pols) és
    multiplicatiu i gairebé acromàtic (el flat de la Sony ho és: B/G 2,3 %) → mateixa profunditat relativa als tres canals. Un buit real
    de la corona K (color solar) sobre un cel més blau → més profund en relatiu a R que a B. Control: T2 abans del flat 2D (patró del flat).
(c) Brno pot jutjar a 7 R☉? Correlació del detall fi (σ 4/40) entre Brno 200 mm (capa 230) i la nostra base a la caixa de T1 i T2.
Sortida: S5_COLOR_I_AMENYSB.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
res = {}
# (a) A − B a T1
for var in ('ctrl', 'f2d'):
    tr = TRACOS[1]; box = caixa_tr(tr, 700)
    a, ca = obre(f'A_{var}'); b, cb = obre(f'B_{var}')
    rA = rel_map(retall(a, ca, box)); rB = rel_map(retall(b, cb, box)); dAB = rA - rB
    for nom, r in (('A', rA), ('B', rB), ('A_menys_B', dAB), ('A_mes_B_mitja', 0.5 * (rA + rB))):
        m, t, pr = mesura_amb_nul(r, box[:2], tr['centre'], tr['d'], tr['llarg'])
        res.setdefault('AmenysB_T1', {})[f'{nom}_{var}'] = m
        print(f"T1 {nom:14s} {var}: D {m['D']*1e4:+6.2f}‱ · nul ±{m.get('nul_mad', np.nan)*1e4:.2f} · z {m.get('z', np.nan):+.1f} · p {m.get('p', np.nan):.3f}", flush=True)
# (b) color
for nomf in ('A_ctrl', 'A_f2d', 'B_ctrl', 'B_f2d', 'SonyAB_ctrl', 'SonyAB_f2d'):
    p, _ = FONTS[nomf]; a = np.load(p, mmap_mode='r')
    for k, tr in TRACOS.items():
        if nomf.startswith('B_') and k == 2: continue
        box = caixa_tr(tr, 700); row = {}
        for ch, cn in enumerate('RGB'):
            img = retall(a, ch, box); r = rel_map(img)
            m, t, pr = mesura_amb_nul(r, box[:2], tr['centre'], tr['d'], tr['llarg'], girs=())
            x0, y0, x1, y1 = box; row[cn] = dict(D=m['D'], nul_mad=m.get('nul_mad'), z=m.get('z'), nivell_mediana=float(np.nanmedian(img[img > 0])))
        row['R_sobre_G'] = row['R']['D'] / row['G']['D'] if row['G']['D'] else None; row['B_sobre_G'] = row['B']['D'] / row['G']['D'] if row['G']['D'] else None
        eR = abs(row['R_sobre_G']) * np.hypot(row['R']['nul_mad'] / row['R']['D'], row['G']['nul_mad'] / row['G']['D']); eB = abs(row['B_sobre_G']) * np.hypot(row['B']['nul_mad'] / row['B']['D'], row['G']['nul_mad'] / row['G']['D'])
        row['err_R_sobre_G'] = float(eR); row['err_B_sobre_G'] = float(eB); row['color_local_R_G_B'] = [row[c]['nivell_mediana'] for c in 'RGB']
        res.setdefault('color', {})[f'{nomf}_T{k}'] = row
        print(f"color {nomf:12s} T{k}: D R/G/B {row['R']['D']*1e4:+.1f} / {row['G']['D']*1e4:+.1f} / {row['B']['D']*1e4:+.1f}‱ (nul ±{row['R']['nul_mad']*1e4:.1f}/{row['G']['nul_mad']*1e4:.1f}/{row['B']['nul_mad']*1e4:.1f}) · R/G {row['R_sobre_G']:.2f}±{eR:.2f} · B/G {row['B_sobre_G']:.2f}±{eB:.2f} · color local {np.round(np.array(row['color_local_R_G_B'])/row['color_local_R_G_B'][1], 3)}", flush=True)
# (c) Brno a 7 R☉
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); from jutge_comu import Estat
ES = Estat(ARREL / '4-RESULTATS/v103_banda_20260926/E/estat_v103')
for k, tr in TRACOS.items():
    box = caixa_tr(tr, 700); rgb = ES.rgb(230, box); Y = (0.25 * rgb[..., 0] + 0.5 * rgb[..., 1] + 0.25 * rgb[..., 2]).astype(np.float32); Y = np.where(Y > 0.002, Y, 0)
    b, cb = obre('base_f2d'); base = retall(b, cb, box)
    for sfi in (2.0, 4.0, 8.0):
        rb = rel_map(Y, 40, sfi); rs = rel_map(base, 40, sfi); kk = np.isfinite(rb) & np.isfinite(rs)
        cc = float(np.corrcoef(rb[kk], rs[kk])[0, 1]) if kk.sum() > 1000 else None
        sh = np.roll(rs, 150, axis=1); k2 = np.isfinite(rb) & np.isfinite(sh); c0 = float(np.corrcoef(rb[k2], sh[k2])[0, 1]) if k2.sum() > 1000 else None
        res.setdefault('brno_correlacio', {})[f'T{k}_sigma{sfi:g}'] = dict(corr=cc, corr_control_desplacat_150=c0, n=int(kk.sum()))
        print(f"Brno L230 × base_f2d, caixa T{k}, banda σ{sfi:g}/40: correlació {cc} (control desplaçat {c0})", flush=True)
desa(OUT / 'S5_COLOR_I_AMENYSB.json', res)

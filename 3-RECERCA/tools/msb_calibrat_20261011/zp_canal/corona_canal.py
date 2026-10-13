"""Diagnòstic INDICATIU: color de càmera de la corona interior en fotogrames crus del R6
contra el color del Sol que donen els punts zero per canal (ZP_CANAL.json).

No és la prova B(3) del pla (mapes MSB per canal sobre el compost, amb cel per canal
i bootstrap per sectors): és una lectura ràpida per veure si els punts zero són
coherents amb una corona K grisa. Mateixos fotogrames, pedestal, sostre, centre pel
limbe i anells que original/xmatch/corona2.py (r0 … 1,08·r0, mediana azimutal),
però per canal (píxels CFA natius) i NOMÉS a 1,15–1,89 R☉, on la corona domina.

Si la corona és d'espectre solar (K, Thomson), I_c/I_G = F☉,c/F☉,G i
MSB_c/MSB_G = (I_c/I_G)·(fac_c/fac_G) = 1. El cel (més blau) no es resta al
resultat principal; es dona també una versió amb el cel aproximat per la mediana de
l'anell 8,0–8,64 R☉ del mateix fotograma (que conté encara una mica de corona i no
segueix el gradient del cel): és una cota, no un model.

Sortida: resultats/msb_calibrat_20261011/zp_canal/DIAGNOSTIC_COLOR_CORONA.json
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "original"))
import comu  # noqa: E402
os.chdir(comu.work("xmatch"))

import numpy as np  # noqa: E402
import rawpy  # noqa: E402
from scipy import ndimage as ndi, optimize  # noqa: E402

ARREL = comu.ARREL
RES = ARREL / "3-RECERCA/resultats/msb_calibrat_20261011/zp_canal"
RSUN_AS = 947.07
PED = 511.5
SAT = 15800.0
FRAMES = [('572A2970', 1/30.), ('572A2971', 1/8.), ('572A2977', 1/4.)]
RADII = [1.15, 1.3, 1.5, 1.75]
CEL = 8.0
COLS = {'R': (0,), 'G': (1, 3), 'B': (2,)}


def sha256(p, bloc=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bloc)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def limb_center(img, g, guess, Rmoon_px):
    """Còpia literal de corona2.py:limb_center."""
    sm = ndi.uniform_filter(np.where(g, img, np.nan)*1.0, 5)
    sm = np.where(np.isfinite(sm), sm, 0)
    th = np.linspace(0, 2*np.pi, 180, endpoint=False)

    def edge(cx, cy):
        rr = np.linspace(0.80, 1.25, 90)*Rmoon_px
        P = np.array([ndi.map_coordinates(
            sm, [cy+r*np.sin(th), cx+r*np.cos(th)], order=1) for r in rr])
        d = np.gradient(P, axis=0)
        k = np.argmax(d, axis=0)
        return rr[k]

    def cost(p):
        r = edge(p[0], p[1])
        return np.std(r)
    r0 = optimize.minimize(cost, guess, method='Nelder-Mead',
                           options=dict(xatol=0.3, fatol=0.02, maxiter=200))
    cx, cy = r0.x
    return cx, cy, float(np.median(edge(cx, cy)))


def main():
    zp = json.load(open(RES / 'ZP_CANAL.json'))
    sol = json.load(open('final_solution.json'))
    scale = sol['r6']['scale']
    Rsun_px = RSUN_AS/scale
    Fs = {ch: zp['canals'][ch]['F_sol_ADU_s'] for ch in 'RGB'}
    sig = {ch: zp['canals'][ch]['sigma_m_sol'] for ch in 'RGB'}
    entrades = {'resultats/msb_calibrat_20261011/zp_canal/ZP_CANAL.json': sha256(RES / 'ZP_CANAL.json')}
    files = []
    for name, exp in FRAMES:
        path = Path(comu.DADES_VIXEN_UNF) / (name + '.CR3')
        entrades[f'0-RAW/Vixen R6III/Vixen Fase totalitat/{name}.CR3'] = sha256(path)
        with rawpy.imread(str(path)) as r:
            raw = r.raw_image_visible.astype(np.float32)
            col = r.raw_colors_visible.copy()
        g = (col == 1) | (col == 3)
        sat = raw >= SAT
        img = raw - PED
        smm = ndi.uniform_filter(np.where(g, img, 0), 31)
        lo = smm < 0.05*np.percentile(smm, 99.5)
        lab, n = ndi.label(ndi.binary_fill_holes(smm > 0.05*np.percentile(smm, 99.5)) & lo)
        if n:
            sz = ndi.sum(lo, lab, range(1, n+1))
            ys, xs = np.nonzero(lab == 1+int(np.argmax(sz)))
            guess = [xs.mean(), ys.mean()]
        else:
            guess = [img.shape[1]/2, img.shape[0]/2]
        cx, cy, rlimb = limb_center(img, g, guess, 1.03*Rsun_px)
        H, W = img.shape
        Y, X = np.mgrid[0:H, 0:W]
        R = np.hypot(X-cx, Y-cy)/Rsun_px
        okb = ~ndi.binary_dilation(sat, iterations=4)
        rec = dict(fotograma=name, exp=exp, centre_limbe=[float(cx), float(cy)], r_limbe_Rsol=rlimb/Rsun_px,
                   anells={})
        for r0 in RADII + [CEL]:
            mring = okb & (R >= r0) & (R < r0*1.08)
            v = {}
            for ch in 'RGB':
                m = mring & np.isin(col, COLS[ch])
                v[ch] = float(np.median(img[m]))/exp if m.sum() > 500 else float('nan')
            rec['anells'][f'{r0:.2f}'] = v
        cel = rec['anells'][f'{CEL:.2f}']
        for r0 in RADII:
            v = rec['anells'][f'{r0:.2f}']
            for tag, sub in (('sense_cel', {c: 0.0 for c in 'RGB'}), ('menys_anell_8Rsol', cel)):
                IR, IG, IB = (v[c] - sub[c] for c in 'RGB')
                v[f'R_G_{tag}'] = IR/IG
                v[f'B_G_{tag}'] = IB/IG
                v[f'MSB_R_sobre_MSB_G_{tag}'] = (IR/IG)/(Fs['R']/Fs['G'])
                v[f'MSB_B_sobre_MSB_G_{tag}'] = (IB/IG)/(Fs['B']/Fs['G'])
            v['fraccio_cel_G_estimada'] = cel['G']/v['G']
        files.append(rec)
        print(f'{name} {exp:.4f}s centre ({cx:.1f}, {cy:.1f})  ' + '  '.join(
            f"{r0:.2f}: R/G {rec['anells'][f'{r0:.2f}']['R_G_sense_cel']:.3f} B/G {rec['anells'][f'{r0:.2f}']['B_G_sense_cel']:.3f}"
            for r0 in RADII))
        del raw, img, g, sat, R, X, Y, col
    srel = {ch: 0.4*np.log(10)*np.hypot(sig[ch], sig['G']) for ch in 'RB'}
    resum = {}
    for tag in ('sense_cel', 'menys_anell_8Rsol'):
        for ch in 'RB':
            vals = [f['anells'][f'{r0:.2f}'][f'MSB_{ch}_sobre_MSB_G_{tag}'] for f in files for r0 in RADII]
            resum[f'MSB_{ch}_sobre_MSB_G_{tag}'] = dict(mediana=float(np.median(vals)), min=float(np.min(vals)),
                                                         max=float(np.max(vals)),
                                                         sigma_rel_dels_punts_zero=float(srel[ch]))
    # El color cru publicat a research/76 §5 ter (compost HDR, 1,1–1,3 R☉): R/G 0,816, B/G 0,361
    pub = dict(font='3-RECERCA/76_HDR_CORONA_VIXEN_2026-08-16.md §5 ter (color cru, 1,1–1,3 R☉)',
               R_G=0.816, B_G=0.361,
               MSB_R_sobre_MSB_G=0.816/(Fs['R']/Fs['G']), MSB_B_sobre_MSB_G=0.361/(Fs['B']/Fs['G']))
    # Interval amb el bootstrap conjunt (post hoc) de SENSIBILITAT_ZP.json, si hi és:
    # MSB_c/MSB_G = (I_c/I_G) / (F☉,c/F☉,G), amb I_c/I_G mesurat a 1,15–1,3 R☉ (mediana dels 3 fotogrames).
    sens = RES / 'SENSIBILITAT_ZP.json'
    if sens.exists():
        sj = json.load(open(sens))
        entrades['resultats/msb_calibrat_20261011/zp_canal/SENSIBILITAT_ZP.json'] = sha256(sens)
        bt = sj['r6']['bootstrap_conjunt']
        for ch in 'RB':
            ic = float(np.median([f['anells'][f'{r0:.2f}'][f'{ch}_G_sense_cel'] for f in files for r0 in (1.15, 1.3)]))
            b = bt[f'F_sol_{ch}_sobre_G']
            resum[f'MSB_{ch}_sobre_MSB_G_amb_bootstrap'] = dict(
                I_sobre_IG_1_15_1_3=ic, p50=ic/b['p50'], interval_68=[ic/b['p84'], ic/b['p16']],
                interval_95=[ic/b['p97_5'], ic/b['p2_5']], nota='post hoc; interval de la dispersió de punts zero')
    out = dict(tasca='msb_calibrat_20261011/zp_canal', guio='tools/msb_calibrat_20261011/zp_canal/corona_canal.py',
               data=time.strftime('%Y-%m-%dT%H:%M:%S'), caracter='INDICATIU (no és la prova B(3) del pla)',
               color_sol_camera=dict(F_R_sobre_F_G=Fs['R']/Fs['G'], F_B_sobre_F_G=Fs['B']/Fs['G'],
                                     sigma_rel_R=float(srel['R']), sigma_rel_B=float(srel['B'])),
               fotogrames=files, resum=resum, color_publicat_research76=pub, entrades=entrades)
    json.dump(out, open(RES / 'DIAGNOSTIC_COLOR_CORONA.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(resum, indent=1))
    print('publicat (76):', json.dumps(pub, ensure_ascii=False))


if __name__ == '__main__':
    main()

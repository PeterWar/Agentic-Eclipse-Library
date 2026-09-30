"""p2 (V100 detall · PÍXELS) · el detall de la banda a la V80 (i V69–V78, V98, V99): és DADA REAL?
Prova clau: correlació del pas alt de cada versió amb el de la dada independent D29 (verd lineal de TOTS els fotogrames Vixen que veuen
el píxel a D_real ≥ 1 px del seu limbe real, D29_candidat_banda.npz), per sector i per calaix de distància d al cercle de presentació.
- Tot es mostreja en polars al voltant del cercle de presentació: d de −6 a 25 px (pas 0,25), arc de 0,5 px (remap bilineal, normalitzat per la validesa).
- Pas alt TANGENCIAL (al llarg de l'arc, al mateix d: la vora de la Lluna no hi entra) σ 1,5 · 2 · 3 px; i ISOTRÒPIC σ 1,5 · 3 (convolució normalitzada
  dins de la validesa de D29, la mateixa màscara per a totes les versions).
- Sostre de soroll: correlació entre les meitats independents G_parells i G_senars → fiabilitat de D29 (Spearman-Brown) i correlació màxima esperable.
- Control nul: D29 desplaçada ±20…40 px AL LLARG DE L'ARC (22 desplaçaments).
- Continuació radial: correlació del pas alt tangencial de cada calaix amb el de l'anell de referència d 8–10 px (mateix PA), i correlació parcial
  V·D29 descomptant-hi l'anell exterior (de D29 i de la versió): si el detall de la banda fos una continuació del de fora, la parcial cauria a 0.
- Energia de textura (rms del pas alt, unitats de ln) i la seva raó amb la del calaix 10–20 px.
Tot es llegeix (NOMÉS LECTURA); la V80 és el retall exacte del llenç (P1: registre 0,03 px, residu 0,05 px, cap remostreig).
Sortida: 4-RESULTATS/v100_detall_20260925/pixels/P2_CORRELACIO.json i P2_TAULA.md (només fitxers nous)."""
import json, sys, time
from pathlib import Path
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter, gaussian_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parent))
from p0_comu_pixels import FIN, SORT, LX, LY, RL, SIL, llegeix_finestra, ln_lum, geometria, d29_a_finestra, FONTS

y0, y1, x0, x1 = FIN
DS, DD = 0.5, 0.25
DGRID = np.arange(-6.0, 25.0 + 1e-9, DD)
NTH = int(round(2 * np.pi * RL / DS)); TH = np.arange(NTH) * 2 * np.pi / NTH; PAg = np.degrees(TH)
SECTORS = {'dalt_75_135': (75, 135), 'baixesq_205_255': (205, 255), 'dreta_300_360_control': (300, 360)}
CALAIXOS = [(-2, -1), (-1, 0), (0, 1), (1, 2), (2, 3), (3, 5), (5, 8), (10, 20)]
REF_EXT = (8, 10)
SH_NUL = [s for s in range(20, 41, 2)]
VERSIONS = ['V80', 'V75C', 'V78', 'V71', 'V69', 'V98', 'V99']


def a_polars(img, m=None):
    """mostreig bilineal a (d, θ); amb màscara: normalitzat (NaN on la validesa < 0,5)."""
    rr = RL + DGRID[:, None]
    mx = (LX + rr * np.cos(TH[None, :]) - x0).astype(np.float32)
    my = (LY - rr * np.sin(TH[None, :]) - y0).astype(np.float32)
    if m is None:
        return cv2.remap(img.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan).astype(np.float64)
    a = cv2.remap(np.where(m, img, 0).astype(np.float32), mx, my, cv2.INTER_LINEAR, borderValue=0).astype(np.float64)
    w = cv2.remap(m.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderValue=0).astype(np.float64)
    return np.where(w > 0.5, a / np.maximum(w, 1e-9), np.nan)


def hp_tang(P, sig_px):
    m = np.isfinite(P); a = np.where(m, P, 0.0); s = sig_px / DS
    num = gaussian_filter1d(a, s, axis=1, mode='wrap'); den = gaussian_filter1d(m.astype(float), s, axis=1, mode='wrap')
    return np.where(m & (den > 0.3), P - num / np.maximum(den, 1e-9), np.nan)


def hp_iso(img, m, sig):
    a = np.where(m, img, 0.0); w = m.astype(float)
    lo = gaussian_filter(a, sig) / np.maximum(gaussian_filter(w, sig), 1e-9)
    return np.where(m, img - lo, np.nan)


def pear(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 30:
        return np.nan, int(ok.sum())
    a, b = a[ok] - a[ok].mean(), b[ok] - b[ok].mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-300)), int(ok.sum())


def parcial(a, b, c):
    """correlació parcial de a i b descomptant c (regressió lineal)."""
    ok = np.isfinite(a) & np.isfinite(b) & np.isfinite(c)
    if ok.sum() < 30:
        return np.nan
    A = np.c_[np.ones(ok.sum()), c[ok]]
    ra = a[ok] - A @ np.linalg.lstsq(A, a[ok], rcond=None)[0]; rb = b[ok] - A @ np.linalg.lstsq(A, b[ok], rcond=None)[0]
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    t0 = time.time()
    d, pa = geometria()
    # D29 i meitats (ln del verd lineal post-matriu)
    G, Gp, Gs = (d29_a_finestra(k) for k in ('G', 'G_parells', 'G_senars'))
    NF = d29_a_finestra('NF')
    mG = np.isfinite(G) & (G > 0); mH = mG & (Gp > 0) & (Gs > 0)
    lnG = np.where(mG, np.log(np.where(mG, G, 1)), np.nan)
    lnGp = np.where(mH, np.log(np.where(mH, Gp, 1)), np.nan); lnGs = np.where(mH, np.log(np.where(mH, Gs, 1)), np.nan)
    ln = {v: ln_lum(llegeix_finestra(v)) for v in VERSIONS if FONTS[v][0].exists()}
    vers = list(ln)
    # polars
    P = {'D29': a_polars(lnG, mG), 'D29p': a_polars(lnGp, mH), 'D29s': a_polars(lnGs, mH)}
    for v in vers:
        P[v] = a_polars(ln[v])
    NFp = a_polars(NF.astype(float), np.isfinite(NF))
    HP = {}
    for sg in (1.5, 2.0, 3.0):
        for k in P:
            HP[('tang', sg, k)] = hp_tang(P[k], sg)
    mC = mH  # màscara comuna per a l'isotròpic: on D29 i totes dues meitats tenen dada
    for sg in (1.5, 3.0):
        HP[('iso', sg, 'D29')] = a_polars(hp_iso(lnG, mC, sg), mC)
        HP[('iso', sg, 'D29p')] = a_polars(hp_iso(lnGp, mC, sg), mC)
        HP[('iso', sg, 'D29s')] = a_polars(hp_iso(lnGs, mC, sg), mC)
        for v in vers:
            HP[('iso', sg, v)] = a_polars(hp_iso(ln[v], mC, sg), mC)
            HP[('isolliure', sg, v)] = a_polars(ln[v] - gaussian_filter(ln[v], sg))  # tal com és (inclou la vora de la Lluna): només per a l'energia
    out = {'geometria': dict(LX=LX, LY=LY, RL=RL, DS_arc=DS, DD=DD), 'calaixos': CALAIXOS, 'sectors': SECTORS, 'desplacaments_nul_px': SH_NUL,
           'versions': vers, 'resultats': {}}
    iref = (DGRID >= REF_EXT[0]) & (DGRID < REF_EXT[1])
    for (tipus, sg) in [('tang', 1.5), ('tang', 2.0), ('tang', 3.0), ('iso', 1.5), ('iso', 3.0)]:
        H = {k: HP[(tipus, sg, k)] for k in ['D29', 'D29p', 'D29s'] + vers}
        ext = {k: np.nanmean(H[k][iref], axis=0) for k in H}  # anell de referència d 8–10 (mitjana radial), per PA
        for sn, (a0, a1) in SECTORS.items():
            cs = (PAg >= a0) & (PAg < a1)
            for (lo, hi) in CALAIXOS:
                ri = (DGRID >= lo) & (DGRID < hi)
                blk = lambda k, roll=0: (np.roll(H[k], roll, axis=1) if roll else H[k])[ri][:, cs]
                res = {}
                rh, nh = pear(blk('D29p'), blk('D29s'))
                rel = 2 * rh / (1 + rh) if np.isfinite(rh) and rh > -0.99 else np.nan
                nfb = NFp[ri][:, cs]
                res['D29'] = dict(n=nh, NF_mediana=float(np.nanmedian(nfb)) if np.isfinite(nfb).any() else 0.0,
                                  r_meitats=rh, fiabilitat=rel, sostre_r=float(np.sqrt(rel)) if np.isfinite(rel) and rel > 0 else np.nan,
                                  energia=float(np.nanstd(blk('D29'))), r_radial_ext=pear(blk('D29'), np.broadcast_to(ext['D29'][cs], blk('D29').shape))[0])
                for v in vers:
                    r, n = pear(blk(v), blk('D29'))
                    rp, _ = pear(blk(v), blk('D29p')); rs, _ = pear(blk(v), blk('D29s'))
                    nul = []
                    for s in SH_NUL:
                        for sgn in (1, -1):
                            nul.append(pear(blk(v), blk('D29', sgn * int(round(s / DS))))[0])
                    nul = np.array(nul)
                    e_v = np.broadcast_to(ext[v][cs], blk(v).shape); e_d = np.broadcast_to(ext['D29'][cs], blk(v).shape)
                    rr_ = dict(r=r, n=n, r_parells=rp, r_senars=rs, nul_mitjana=float(np.nanmean(nul)), nul_sd=float(np.nanstd(nul)),
                               nul_max_abs=float(np.nanmax(np.abs(nul))), z=float((r - np.nanmean(nul)) / max(np.nanstd(nul), 1e-6)),
                               r_desatenuada=float(r / np.sqrt(rel)) if np.isfinite(rel) and rel > 0.02 else np.nan,
                               energia=float(np.nanstd(blk(v))), r_radial_ext=pear(blk(v), e_v)[0],
                               parcial_sense_ext_D29=parcial(blk(v).ravel(), blk('D29').ravel(), e_d.ravel()),
                               parcial_sense_ext_V=parcial(blk(v).ravel(), blk('D29').ravel(), e_v.ravel()))
                    if tipus == 'iso':
                        rr_['energia_lliure'] = float(np.nanstd(HP[('isolliure', sg, v)][ri][:, cs]))
                    res[v] = rr_
                out['resultats'][f'{tipus}{sg}|{sn}|{lo}_{hi}'] = res
    # raons d'energia respecte de 10–20
    for key in list(out['resultats']):
        t, sn, cb = key.split('|')
        ref = out['resultats'].get(f'{t}|{sn}|10_20')
        for k, v in out['resultats'][key].items():
            v['energia_rel_10_20'] = v['energia'] / ref[k]['energia'] if ref and ref[k]['energia'] > 0 else np.nan
    out['segons'] = round(time.time() - t0, 1)

    def neteja(o):
        if isinstance(o, dict):
            return {k: neteja(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [neteja(v) for v in o]
        if isinstance(o, float):
            return None if not np.isfinite(o) else round(o, 4)
        return o
    p = SORT / 'P2_CORRELACIO.json'
    if p.exists():
        p = SORT / f'P2_CORRELACIO_{int(time.time())}.json'
    p.write_text(json.dumps(neteja(out), indent=1, ensure_ascii=False))
    # taula llegible
    L = ['# P2 · el detall de la banda: correlació amb la dada independent D29', '',
         'r = correlació del pas alt (V · D29); nul = D29 desplaçada ±20–40 px al llarg de l\'arc (mitjana ± sd); sostre = √fiabilitat de D29 (meitats); '
         'r_des = r/sostre; E = energia (rms del pas alt, ln) i E/E₁₀₋₂₀; parc = correlació parcial descomptant l\'anell exterior 8–10 px de D29.', '']
    for t in ['tang1.5', 'tang2.0', 'tang3.0', 'iso1.5', 'iso3.0']:
        for sn in SECTORS:
            L += [f'## {t} · {sn}', '', '| d (px) | NF | r meitats | sostre | ' + ' | '.join(f'{v} r (nul) · r_des · parc · E/E₁₀' for v in vers) + ' | D29 E/E₁₀ |',
                  '|' + '---|' * (4 + len(vers) + 1)]
            for (lo, hi) in CALAIXOS:
                R = out['resultats'][f'{t}|{sn}|{lo}_{hi}']; D = R['D29']
                f = lambda x, n=2: '—' if x is None or not np.isfinite(x) else f'{x:.{n}f}'
                cel = []
                for v in vers:
                    q = R[v]; cel.append(f"{f(q['r'])} ({f(q['nul_mitjana'])}±{f(q['nul_sd'])}) · {f(q['r_desatenuada'])} · {f(q['parcial_sense_ext_D29'])} · {f(q['energia_rel_10_20'])}")
                L.append(f"| {lo}–{hi} | {f(D['NF_mediana'], 0)} | {f(D['r_meitats'])} | {f(D['sostre_r'])} | " + ' | '.join(cel) + f" | {f(D['energia_rel_10_20'])} |")
            L.append('')
    q = SORT / 'P2_TAULA.md'
    if q.exists():
        q = SORT / f'P2_TAULA_{int(time.time())}.md'
    q.write_text('\n'.join(L))
    print('fet', p, q, out['segons'], 's')


if __name__ == '__main__':
    main()

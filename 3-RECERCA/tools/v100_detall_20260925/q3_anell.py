"""q3 (V100 detall, dada) · La correcció de transmissió de la D29 fa un ANELL (salt de nivell) a la vora antiga de la V99?
Compara, als MATEIXOS píxels, el verd post-matriu lineal de la candidata (D29 = rampa 1→2,5, i les altres rampes de q0) amb el de la V99
(A3C_franja_silueta.npz, E[...,1] = mateixes unitats que la D29; la G de la V99 = c_G·E a menys de 60 px, c_G = 1,0097).
  · u = d − DMIN(PA): distància a la vora del domini de la V99 (DMIN per 0,25° de PA, la de l'a3c). u < 0 = la banda (només la D29).
  · Per sector i calaix de 0,5 px: mediana de ln(G_D29/E_V99) als píxels comuns (domini_E de la V99 i G_D29 > 0), p16/p84 i n.
  · Perfil radial de cada una (mediana ln G per calaix de 0,5 px de d), i el salt que faria empalmar la D29 a la banda i la V99 a fora:
    mediana ln G_D29 a u ∈ [−0,5, 0) contra ln E_V99 a u ∈ [0, 0,5), corregit pel pendent radial local de la mateixa V99.
Sortida: 4-RESULTATS/v100_detall_20260925/dada/Q3_ANELL.json i Q3_resum.txt."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925/dada'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
SORT = O / 'Q3_ANELL.json'; assert not SORT.exists()
Z = np.load(O / 'Q0_meitats_rampes.npz'); idx = Z['idx']; by0, by1, bx0, bx1 = Z['box']; hb, wb = by1 - by0, bx1 - bx0; LX, LY, RL = Z['centre']
A = np.load(R9 / 'B/lineal_v99_franja/A3C_franja_silueta.npz'); assert list(A['box']) == [by0, by1, bx0, bx1]
E = A['E'][..., 1].ravel()[idx].astype(np.float64); DOM = A['domini_E'].ravel()[idx]; DMIN = A['DMIN']
yy, xx = np.mgrid[by0:by1, bx0:bx1]; y = yy.ravel()[idx]; x = xx.ravel()[idx]
d = np.hypot(x - LX, y - LY) - RL; th = (np.degrees(np.arctan2(-(y - LY), x - LX)) + 360) % 360
u = d - DMIN[(th / 360 * DMIN.size).astype(int) % DMIN.size]
S = np.load(R9 / 'D21_silueta_o2.npz'); dsil = d - np.interp(th, S['pa'], S['e'], period=360)
SECTORS = [(75, 105), (105, 135), (150, 210), (205, 235), (235, 255), (285, 345)]
RAMPES = [tuple(r) for r in Z['rampes']]
def med(v): return (float(np.median(v)), float(np.percentile(v, 16)), float(np.percentile(v, 84)), int(v.size)) if v.size >= 30 else None
res = dict(metode=__doc__, sectors=SECTORS, rampes=RAMPES, per_sector=[])
L = []
for a0, a1 in SECTORS:
    zs = (th >= a0) & (th < a1); sec = dict(sector=[a0, a1], DMIN_mediana=float(np.median(u[zs] * 0 + (d[zs] - u[zs]))), perfils={})
    lnE = np.where(DOM & (E > 0), np.log(np.maximum(E, 1e-30)), np.nan)
    for r, rp in enumerate(RAMPES):
        G = Z[f'G_tot_r{r}'].astype(np.float64); lnG = np.where(G > 0, np.log(np.maximum(G, 1e-30)), np.nan)
        rat_u, rat_d, prof_d, prof_u = [], [], [], []
        for b0 in np.arange(-6, 12, 0.5):                     # respecte de la vora de la V99
            q = zs & (u >= b0) & (u < b0 + 0.5); c = q & np.isfinite(lnG) & np.isfinite(lnE)
            rat_u.append(dict(u=[float(b0), float(b0 + 0.5)], ln_D29_sobre_V99=med(lnG[c] - lnE[c]) if c.any() else None,
                              ln_D29=med(lnG[q & np.isfinite(lnG)]), ln_V99=med(lnE[q & np.isfinite(lnE)])))
        for b0 in np.arange(-2, 20, 0.5):                     # respecte del cercle de presentació
            q = zs & (d >= b0) & (d < b0 + 0.5); c = q & np.isfinite(lnG) & np.isfinite(lnE)
            rat_d.append(dict(d=[float(b0), float(b0 + 0.5)], ln_D29_sobre_V99=med(lnG[c] - lnE[c]) if c.any() else None,
                              ln_D29=med(lnG[q & np.isfinite(lnG)]), ln_V99=med(lnE[q & np.isfinite(lnE)])))
        # salt d'empalmar: D29 a u∈[−0,5,0) contra V99 a u∈[0,0,5), menys el pendent de la V99 entre u∈[0,0,5) i u∈[0,5,1)
        def m_(arr, lo, hi): q = zs & (u >= lo) & (u < hi) & np.isfinite(arr); return float(np.median(arr[q])) if q.sum() >= 30 else np.nan
        pend = m_(lnE, 0.5, 1.0) - m_(lnE, 0.0, 0.5); salt = (m_(lnG, -0.5, 0.0) - m_(lnE, 0.0, 0.5)) + pend
        # referència lluny de la vora (u 6–10): el quocient hi hauria de ser el mateix a tot arreu si no hi ha anell
        def rq(lo, hi):
            q = zs & (u >= lo) & (u < hi) & np.isfinite(lnG) & np.isfinite(lnE); return float(np.median(lnG[q] - lnE[q])) if q.sum() >= 30 else None
        ref = rq(6, 10)
        sec['perfils'][f'rampa_{rp[0]}_{rp[1]}'] = dict(per_u=rat_u, per_d=rat_d, quocient_u_6_10=ref,
                                                         quocient_menys_ref={f'{lo}..{hi}': (None if (rq(lo, hi) is None or ref is None) else rq(lo, hi) - ref)
                                                                             for lo, hi in ((0, 0.5), (0.5, 1), (1, 1.5), (1.5, 2), (2, 3), (3, 4), (4, 6))},
                                                         salt_empalmar_ln=None if not np.isfinite(salt) else salt, pendent_V99_per_0_5px=None if not np.isfinite(pend) else pend)
        qm = sec['perfils'][f'rampa_{rp[0]}_{rp[1]}']['quocient_menys_ref']
        L.append(f"PA{a0}-{a1} rampa {rp}: ln(D29/V99) u6–10 = {ref if ref is None else round(ref, 4)} · menys ref per u: "
                 + ' '.join(f"{k}:{'--' if v is None else f'{100 * v:+.2f}%'}" for k, v in qm.items())
                 + f" · salt empalmar {'--' if not np.isfinite(salt) else f'{100 * salt:+.2f}%'} (pendent V99 {'--' if not np.isfinite(pend) else f'{100 * pend:+.2f}%'}/0,5px)")
    res['per_sector'].append(sec)
SORT.write_text(json.dumps(res, indent=1, ensure_ascii=False)); (O / 'Q3_resum.txt').write_text('\n'.join(L)); print('\n'.join(L))

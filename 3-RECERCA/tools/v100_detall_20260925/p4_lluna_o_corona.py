"""p4 (V100 detall · PÍXELS) · el senyal reproduïble de la dada a la banda: és CORONA (fix al cel) o VORA DE LA LLUNA (es mou amb la Lluna)?
Mateixa selecció i pesos que d29 (tots els fotogrames Vixen amb D_real ≥ 1 px, rampa 1→2,5, dividits per T_classe(D_real), pes w·s·T², verd
post-matriu), però cada fotograma es mostreja en polars de DUES maneres:
  (a) CEL: al voltant del cercle de presentació (fix): la corona hi suma en fase; la vora lunar (que es mou 28 px) s'hi esborra;
  (b) LLUNA: al voltant del centre del model de la Lluna d'AQUELL fotograma: la vora lunar hi suma en fase; la corona s'hi esborra.
En totes dues s'acumulen les meitats independents (parells/senars dins de cada classe, com d29) i es mesura S² = cov(meitats) del pas alt
tangencial, per sector i calaix. Si S²_cel > S²_lluna, el detall reproduïble de la banda és corona; si és al revés, és la vora de la Lluna.
Control: dreta 300–360 (la Lluna s'hi allunya; hi ha desenes de fotogrames nets).
Només lectura de 4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna i dels fitxers de la V99. Sortida: pixels/P4_LLUNA_O_CORONA.json."""
import json, os, sys, time
from pathlib import Path
import numpy as np
import cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from p0_comu_pixels import ARREL, SORT, LX, LY, RL
import p2_v80_correlacio as P2

LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float64); gn = np.array(meta['gain'], np.float64)
DR = Rm - RL
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']; TC = json.loads((R9 / 'TCORR_V99.json').read_text())
LO, HI = 1.0, 2.5
DGRID, TH, PAg, DS = P2.DGRID, P2.TH, P2.PAg, P2.DS
SECT = {'dalt_75_105': (75, 105), 'dalt_105_135': (105, 135), 'baixesq_205_255': (205, 255), 'dreta_300_360_control': (300, 360)}
CAL = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 8), (10, 20)]


def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)


def mapa(cx, cy):
    rr = RL + DGRID[:, None]
    return ((cx + rr * np.cos(TH[None, :]) - bx0).astype(np.float32), (cy - rr * np.sin(TH[None, :]) - by0).astype(np.float32))


def main():
    t0 = time.time()
    N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
    hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
    cls = [classe(f['exposure']) for f in fr]; par = {}; cnt = {}
    for j, c in enumerate(cls):
        cnt[c] = cnt.get(c, 0) + 1; par[j] = cnt[c] % 2
    shp = (len(DGRID), len(TH))
    acc = {(g, h): [np.zeros(shp + (3,)), np.zeros(shp + (3,))] for g in ('cel', 'lluna') for h in (0, 1)}
    mcel = mapa(LX, LY); centres = []
    for j in range(len(fr)):
        Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = hb // 2, wb - 100
        cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]; centres.append((cx, cy, fr[j]['time']))
        pa = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
        Dr = Dj + DR - np.interp(pa.ravel(), pag, eg, period=360).reshape(hb, wb)
        s = smoothstep(Dr, LO, HI); t = TC[cls[j]]; T = np.exp(np.interp(Dr, t['D'], t['lnT'], left=t['lnT'][0], right=0.0)); T = np.where(s > 0, T, 1.0)
        if not (s > 0).any():
            continue
        mll = mapa(cx, cy)
        for c in range(3):
            w = np.asarray(Wt[j, :, :, c], np.float64); n = np.asarray(N[j, :, :, c], np.float64)
            ws = (w * s * T * T).astype(np.float32); ns = (n * s * T).astype(np.float32)
            for g, (mx, my) in (('cel', mcel), ('lluna', mll)):
                a = acc[(g, par[j])]
                a[0][..., c] += cv2.remap(ns, mx, my, cv2.INTER_LINEAR, borderValue=0)
                a[1][..., c] += cv2.remap(ws, mx, my, cv2.INTER_LINEAR, borderValue=0)
    def verd(a):
        num, den = a; E = np.where(den > 0, num / np.maximum(den, 1e-30), np.nan)
        Gp = (E * gn) @ Mx[1]
        return np.where((den[..., 1] > 0) & (Gp > 0), np.log(np.where(Gp > 0, Gp, 1)), np.nan)
    out = {'nota': 'S2 = cov(pas alt tangencial meitat parells, meitat senars); cel = polars fixes al cercle de presentació; lluna = polars al centre de la Lluna de cada fotograma',
           'moviment_lluna_px': float(np.hypot(centres[-1][0] - centres[0][0], centres[-1][1] - centres[0][1])), 'r': {}}
    L = {(g, h): verd(acc[(g, h)]) for g in ('cel', 'lluna') for h in (0, 1)}
    for sg in (1.5, 3.0, 6.0):
        H = {k: P2.hp_tang(v, sg) for k, v in L.items()}
        for sn, (a0, a1) in SECT.items():
            cs = (PAg >= a0) & (PAg < a1)
            for lo, hi in CAL:
                ri = (DGRID >= lo) & (DGRID < hi); res = {}
                for g in ('cel', 'lluna'):
                    p, q = H[(g, 0)][ri][:, cs], H[(g, 1)][ri][:, cs]; ok = np.isfinite(p) & np.isfinite(q)
                    if ok.sum() < 40:
                        res[g] = None; continue
                    pc, qc = p[ok] - p[ok].mean(), q[ok] - q[ok].mean()
                    S2 = float(np.mean(pc * qc)); tot = float(np.sqrt(np.mean(pc * pc) * np.mean(qc * qc)))
                    res[g] = dict(S2=S2, r_meitats=S2 / tot if tot > 0 else None, n=int(ok.sum()))
                if res['cel'] and res['lluna']:
                    res['quocient_cel_lluna'] = res['cel']['S2'] / res['lluna']['S2'] if res['lluna']['S2'] > 0 else None
                out['r'][f'tang{sg}|{sn}|{lo}_{hi}'] = res
    # moviment de la Lluna al llarg de l'arc entre fotogrames primerencs i tardans, per sector
    c0 = np.array([(c[0], c[1]) for c in centres if c[2] < 32]).mean(0); c1 = np.array([(c[0], c[1]) for c in centres if c[2] > 100]).mean(0)
    dv = c1 - c0
    out['desplacament_lluna_primers_tardans_px'] = dict(dx=float(dv[0]), dy=float(dv[1]),
        **{f'al_llarg_arc_PA{a}': float(-dv[0] * np.sin(np.radians(a)) - dv[1] * np.cos(np.radians(a))) for a in (90, 120, 230, 330)},
        **{f'radial_PA{a}': float(dv[0] * np.cos(np.radians(a)) - dv[1] * np.sin(np.radians(a))) for a in (90, 120, 230, 330)})
    out['segons'] = round(time.time() - t0, 1)

    def neteja(o):
        if isinstance(o, dict):
            return {k: neteja(v) for k, v in o.items()}
        if isinstance(o, float):
            return None if not np.isfinite(o) else float(f'{o:.5g}')
        return o
    p = SORT / 'P4_LLUNA_O_CORONA.json'
    if p.exists():
        p = SORT / f'P4_LLUNA_O_CORONA_{int(time.time())}.json'
    p.write_text(json.dumps(neteja(out), indent=1, ensure_ascii=False))
    print('fet', p, out['segons'], 's')


if __name__ == '__main__':
    main()

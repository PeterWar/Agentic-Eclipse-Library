"""cv2_1 · La nostra brillantor del MAPA v2 per anells i caselles, per a totes les comparacions v2 (12-10-2026).

Entrades (NOMÉS LECTURA): v2/mapa/ple/msb_ple_v2.npy, msb_noext_ple_v2.npy, flags_ple_v2.npy; v2/mapa/cel/CEL_v2.json i
JOINT_C0FIX_posthoc.json; la graella de massa d'aire de la v1 (mapa/massa_aire_graella.npz, la mateixa que fa servir la v2);
v2/comparacions/banda/CEL_CANALS_v2.json (cv2_0); i la cau de la Paperera (només per als canals R i G natius a r < 2,6 R☉).

Conjunts (regla de la v1: una casella que TOQUI un sol píxel de NO_DATA, LIMB_GAP, MOON_BAND, PROMINENCE, SONY_GHOST o
OUTSIDE_INSCRIBED queda fora sencera):
  kcor  · anells 1,15–1,25 · 1,25–1,40 · 1,40–1,70 · 1,70–2,00 · 2,0–2,5 R☉, caselles d'1°:
          msb (v2), noe, msbG_cau (control: el mateix calculat des de la cau), msbR = fac_R·(R_cam − S_R)·E (k 0,40, cel R de cv2_0),
          msbR_noe, RG_px (quocient píxel a píxel), sky_bias (b_new, central), E, sony;
  banda · anells 1,15–1,25 · 1,25–1,40 · 1,40–1,70 · 1,70–1,90, sectors de 10°, NOMÉS wv ≥ 0,99 (Vixen pura):
          msbG, msbR, i amb el cel constant (a) de cada canal msbG_a, msbR_a; raw_G, raw_R (canal menys cel, ADU/s, sense E);
  c2    · anells 2,4–2,6 … 4,5–5,5 R☉, caselles d'1°: msb, noe; per a cada cel (b_new, a, b_old, joint_c0fix, joint, c) i
          cada k (0; 0,35 només b_new; 0,40; 0,57; 0,72): FAC_G·(G_cam − S)·10^(0,4k(X − X_ZP)); sky_bias (central, mínim i màxim
          de les variants del model K+F); E; sony;
  fig   · els 44 anells fins de la figura (±1,5 %), caselles d'1°: msb, noe, sky_bias.
Escriu v2/comparacions/caselles_v2.npz i CASELLES_v2.json."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2_comu as cv   # noqa: E402

mc, m2, cc1 = cv.mc, cv.m2, cv.cc1
T0 = time.time()
cv.RES2.mkdir(parents=True, exist_ok=True)
msb = np.load(cv.PLE2 / 'msb_ple_v2.npy', mmap_mode='r')
noe = np.load(cv.PLE2 / 'msb_noext_ple_v2.npy', mmap_mode='r')
flg = np.load(cv.PLE2 / 'flags_ple_v2.npy', mmap_mode='r')
assert msb.shape == (mc.H, mc.W) and flg.dtype == np.uint8
cau = mc.obre_cau()
MA = mc.MassaAire()
CEL2 = cv.cel_v2_complet()
CC = json.load(open(cv.RES2 / 'banda' / 'CEL_CANALS_v2.json'))['cel']
ZPJ = json.load(open(mc.RES / 'zp_canal/ZP_CANAL.json'))
FAC_R = float(ZPJ['canals']['R']['fac'])
FAC_G = mc.FAC_G
g = mc.geo_llenc()
RMAX = 6.15
y0 = max(0, int(mc.SOL_XY[1] - RMAX * 1.01 * mc.RSOL_PX)); y1 = min(mc.H, int(mc.SOL_XY[1] + RMAX * 1.01 * mc.RSOL_PX) + 1)
x0 = max(0, int(mc.SOL_XY[0] - RMAX * 1.01 * mc.RSOL_PX)); x1 = min(mc.W, int(mc.SOL_XY[0] + RMAX * 1.01 * mc.RSOL_PX) + 1)
RC = 2.6                               # zona on es llegeixen els canals de la cau
cx0 = int(mc.SOL_XY[0] - RC * 1.01 * mc.RSOL_PX); cx1 = int(mc.SOL_XY[0] + RC * 1.01 * mc.RSOL_PX) + 1

CONJ = {'kcor': (cv.ANELLS_KCOR, 1.0), 'banda': (cv.ANELLS_BANDA, 10.0), 'c2': (cv.ANELLS_C2, 1.0),
        'fig': ([(round(r * (1 - cv.AMPLE_FIG), 5), round(r * (1 + cv.AMPLE_FIG), 5)) for r in cv.RADIS_FIG], 1.0)}
CELS_C2 = ('b_new', 'a', 'b_old', 'joint_c0fix', 'joint', 'c')
KS = {'b_new': (0.0, 0.35, 0.40, 0.57, 0.72)}
VARS = {'kcor': ['msb', 'noe', 'msbG_cau', 'msbR', 'msbR_noe', 'RG_px', 'sky_bias', 'E', 'sony'],
        'banda': ['msbG', 'msbR', 'msbG_a', 'msbR_a', 'raw_G', 'raw_R'],
        'c2': ['msb', 'noe', 'sky_bias', 'sky_bias_min', 'sky_bias_max', 'E', 'sony'] +
              [f'{s}_k{int(round(100 * k)):03d}' for s in CELS_C2 for k in KS.get(s, (0.0, 0.40, 0.57, 0.72))],
        'fig': ['msb', 'noe', 'sky_bias']}
acc = {c: {v: [] for v in VARS[c] + ['key', 'toca']} for c in CONJ}
VARIANTS_BIAIX = list(CEL2['biaix_KF']['b_new'].keys())
control_G = []
for ya in range(y0, y1, 256):
    yb = min(ya + 256, y1)
    yy = np.arange(ya, yb, dtype=np.float64)[:, None] * np.ones((1, x1 - x0))
    xx = np.ones((yb - ya, 1)) * np.arange(x0, x1, dtype=np.float64)[None, :]
    r, pa = g.polar(xx, yy)
    if np.nanmin(r) > RMAX:
        continue
    m = np.asarray(msb[ya:yb, x0:x1], np.float64); n_ = np.asarray(noe[ya:yb, x0:x1], np.float64); f = np.asarray(flg[ya:yb, x0:x1])
    toca = (f & cv.TOCA) > 0
    valid = ~toca & np.isfinite(m)
    X = mc.kasten_young(MA.altura_bloc(ya, yb, x0, x1))
    E040 = m2.factor_extincio(X, 0.40)
    sb = {vn: FAC_G * E040 * m2.biaix_cel_g(xx, yy, 'b_new', CEL2, vn) for vn in VARIANTS_BIAIX}
    sky_bias = sb['central']
    sbs = np.stack([sb[k] for k in VARIANTS_BIAIX])
    vals = dict(msb=m, noe=n_, sky_bias=sky_bias, sky_bias_min=sbs.min(0), sky_bias_max=sbs.max(0), E=E040,
                sony=((f & mc.BITS['SONY_DOMINATED']) > 0).astype(np.float64))
    # cels × k (conjunt c2)
    if np.nanmax(r) >= 2.4 and np.nanmin(r) <= 5.5:
        Sb = m2.cel_model_v2(xx, yy, 'b_new', CEL2)
        Ek = {k: m2.factor_extincio(X, k) for k in (0.0, 0.35, 0.40, 0.57, 0.72)}
        for s_ in CELS_C2:
            net = n_ + FAC_G * (Sb - m2.cel_model_v2(xx, yy, s_, CEL2))
            for k in KS.get(s_, (0.0, 0.40, 0.57, 0.72)):
                vals[f'{s_}_k{int(round(100 * k)):03d}'] = net * Ek[k]
    # canals de la cau (kcor i banda)
    if np.nanmin(r) < RC:
        F = np.full((yb - ya, x1 - x0, 3), np.nan, np.float64)
        F[:, cx0 - x0:cx1 - x0] = np.asarray(cau['fusion_total_v42'][ya:yb, cx0:cx1], np.float64)
        sup = np.zeros((yb - ya, x1 - x0), bool); sup[:, cx0 - x0:cx1 - x0] = np.asarray(cau['support_v42'][ya:yb, cx0:cx1])
        wv = np.zeros((yb - ya, x1 - x0)); wv[:, cx0 - x0:cx1 - x0] = np.asarray(cau['weight_vixen_v42'][ya:yb, cx0:cx1], np.float64)
        dada = sup & np.all(np.isfinite(F), 2) & np.all(F > 0, 2)
        CAM = mc.canals_camera(np.where(dada[..., None], F, np.nan))
        Gv = mc.verd_camera(np.where(dada[..., None], F, np.nan))
        u, v = m2.uv(xx, yy)
        SR = CC['R']['c0'] + CC['R']['gu'] * u + CC['R']['gv'] * v
        SG = m2.cel_model_v2(xx, yy, 'b_new', CEL2)
        rawR = CAM[..., 0] - SR; rawG = Gv - SG
        msbG_cau = FAC_G * rawG * E040
        msbR = FAC_R * rawR * E040
        vals.update(msbG_cau=msbG_cau, msbR=msbR, msbR_noe=FAC_R * rawR, RG_px=msbR / msbG_cau, msbG=msbG_cau,
                    msbG_a=FAC_G * (Gv - CC['G']['a_c0']) * E040, msbR_a=FAC_R * (CAM[..., 0] - CC['R']['a_c0']) * E040,
                    raw_G=rawG, raw_R=rawR)
        cmp_ = valid & (r < RC) & dada & np.isfinite(msbG_cau)
        if cmp_.any():
            control_G.append(float(np.nanmax(np.abs(msbG_cau[cmp_] / m[cmp_] - 1))))
        bandvalid = wv >= mc.WV_SONY
    else:
        bandvalid = np.zeros(r.shape, bool)
    for c, (an, dpa) in CONJ.items():
        if c in ('kcor', 'banda') and np.nanmin(r) >= RC:
            continue
        key, nb = cc1.clau_caselles(r, pa, an, dpa)
        sel = key >= 0
        if not sel.any():
            continue
        tc = toca.copy()
        if c == 'banda':
            tc = tc | ~bandvalid          # a la banda, un píxel amb wv < 0,99 també és «fora» (la zona és Vixen pura)
            ok = ~tc & np.isfinite(m)
        else:
            ok = valid
        acc[c]['key'].append(key[sel]); acc[c]['toca'].append(toca[sel] if c != 'banda' else (toca | ~bandvalid)[sel])
        for vn in VARS[c]:
            arr = vals[vn]
            acc[c][vn].append(np.where(ok, arr, np.nan)[sel].astype(np.float32))
    print(f'files {ya}-{yb} ({time.time() - T0:.0f} s)', flush=True)

out = {}
resum = {}
for c, (an, dpa) in CONJ.items():
    nb = int(round(360 / dpa)); ng = len(an) * nb
    key = np.concatenate(acc[c]['key']); toca = np.concatenate(acc[c]['toca'])
    ntoca = np.bincount(key[toca], minlength=ng)[:ng]
    ntot = np.bincount(key, minlength=ng)[:ng]
    for vn in VARS[c]:
        val = np.concatenate(acc[c][vn]).astype(np.float64)
        n, q = cc1.percentils_grup(key, val, ng, (50,))
        out[f'{c}_{vn}'] = q[50].reshape(len(an), nb)
        if vn in ('msb', 'msbG'):
            out[f'{c}_nvalid'] = n.reshape(len(an), nb)
        acc[c][vn] = None
    out[f'{c}_ntoca'] = ntoca.reshape(len(an), nb); out[f'{c}_ntot'] = ntot.reshape(len(an), nb)
    out[f'{c}_anells'] = np.array(an)
    base = 'msb' if c != 'banda' else 'msbG'
    if c == 'banda':
        usable = (out[f'{c}_nvalid'].ravel() >= 200) & np.isfinite(out[f'{c}_{base}'].ravel())   # regla de la v1 (c4_banda: ≥ 200 px)
    else:
        usable = (ntoca == 0) & (ntot > 0) & np.isfinite(out[f'{c}_{base}'].ravel())
    out[f'{c}_usable'] = usable.reshape(len(an), nb)
    resum[c] = [dict(anell=list(a), caselles_amb_pixels=int((ntot.reshape(len(an), nb)[i] > 0).sum()),
                     caselles_que_toquen=int((ntoca.reshape(len(an), nb)[i] > 0).sum()),
                     caselles_usables=int(out[f'{c}_usable'][i].sum())) for i, a in enumerate(an)]
    del acc[c]
# control: les caselles usables de kcor i c2 han de ser les de la v1 (els bits de zona no han canviat)
N1 = np.load(cc1.RES / 'caselles_nostra.npz')
control = dict(msbG_cau_contra_msb_ple_v2_max_dif_rel=float(max(control_G)) if control_G else None,
               usable_kcor_igual_v1=bool(np.array_equal(out['kcor_usable'], N1['kcor_usable'][:5])),
               usable_c2_igual_v1=bool(np.array_equal(out['c2_usable'], N1['c2_usable'])),
               usable_fig_igual_v1=bool(np.array_equal(out['fig_usable'], N1['fig_usable'])))
print('control', control, flush=True)
np.savez_compressed(cv.RES2 / 'caselles_v2.npz', **out)
entr = {cv.rel(p): cv.sha256(p) for p in (cv.PLE2 / 'msb_ple_v2.npy', cv.PLE2 / 'msb_noext_ple_v2.npy', cv.PLE2 / 'flags_ple_v2.npy',
                                          m2.CELDIR / 'CEL_v2.json', m2.CELDIR / 'JOINT_C0FIX_posthoc.json', mc.MAPA / 'massa_aire_graella.npz',
                                          cv.RES2 / 'banda' / 'CEL_CANALS_v2.json', mc.RES / 'zp_canal/ZP_CANAL.json')}
entr['fusion_total_v42.npy (Paperera, només lectura)'] = mc.SHA_CAU['fusion_total_v42.npy'] + ' (B3_V42_FROZEN)'
cv.json_dump(dict(guio=cv.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), entrades_sha256=entr,
                  regla='casella fora si toca un sol píxel amb bits ' + str(cv.TOCA) +
                        ' (NO_DATA|LIMB_GAP|MOON_BAND|PROMINENCE|SONY_GHOST|OUTSIDE_INSCRIBED); banda: a més, wv ≥ 0,99 i ≥ 200 px per sector',
                  fac_R=FAC_R, fac_G=FAC_G, cel_R=CC['R'], control=control, resum=resum, segons=round(time.time() - T0, 1)),
             cv.RES2 / 'CASELLES_v2.json')
print(json.dumps(resum, indent=0, ensure_ascii=False)[:3000])
print(f'fet ({time.time() - T0:.0f} s)')

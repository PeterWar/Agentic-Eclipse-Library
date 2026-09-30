# -*- coding: utf-8 -*-
"""Portes de halos sobre el resultat de Pere (V18-DesenfocRadialZoom.psb).

Mesura capa1 (original) vs F = capa1*(1-m) + capa2*m (compost del metode de Pere)
a resolucio 1/2, amb les marques de la ronda 2 (verd/taronja) i la ronda 1
(halos_marca) mapades al retall. Tambe el detall tangencial (preu 4b).
"""
import json
import numpy as np
import cv2

B = '/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/'
D = B + 'cau_v19/desenfoc/'
OUT = D + 'fable5/'

geo = json.load(open(D + 'geometria.json'))
OX, OY = geo['origen_dins_v18']          # (2196, 4124) x,y
SX, SY = geo['sol_crop']                  # sol al retall
RS = geo['rs']                            # 455.5 px/Rsol
W, H = geo['llenc']                       # 8156, 5422

# ---------- 1. carrega a 1/2 ----------
def mitja2(a):
    a = a.astype(np.float32)
    return (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) * 0.25

print('carregant capes...')
c1 = np.load(D + 'capa1_rgb16.npy', mmap_mode='r')
c2 = np.load(D + 'capa2_rgb16.npy', mmap_mode='r')
mk = np.load(D + 'capa2_mask16.npy', mmap_mode='r')

c1h = mitja2(c1[:]) / 65535.0             # (2711, 4078, 3) RGB en [0,1]
c2h = mitja2(c2[:]) / 65535.0
mh = mitja2(mk[:]) / 65535.0              # (2711, 4078)
del c1, c2, mk

F = c1h * (1.0 - mh[..., None]) + c2h * mh[..., None]
print('F fet:', F.shape, 'm mitjana %.4f' % mh.mean())

hh, wh = mh.shape
sxh, syh = SX / 2.0, SY / 2.0
rsh = RS / 2.0
yy, xx = np.mgrid[0:hh, 0:wh].astype(np.float32)
rr = np.hypot(xx - sxh, yy - syh) / rsh          # radi en Rsol
azz = np.degrees(np.arctan2(-(yy - syh), xx - sxh))  # conveni de la tasca
del xx, yy

# ---------- 2. marques al retall, a 1/2 ----------
def marca_half(cami, uint8=False):
    a = np.load(cami, mmap_mode='r')
    cr = np.asarray(a[OY:OY + H, OX:OX + W])
    if uint8:
        cr = cr > 0
    m2 = cr[0::2, 0::2] | cr[1::2, 0::2] | cr[0::2, 1::2] | cr[1::2, 1::2]
    return m2

mverd = marca_half(B + 'cau_v19/marques_verd.npy')
mtar = marca_half(B + 'cau_v19/marques_taronja.npy')
mr1 = marca_half(B + 'cau_v18/halos_marca.npy', uint8=True)
mtot = mverd | mtar | mr1
print('marques al retall (1/2): verd %d taronja %d ronda1 %d' %
      (mverd.sum(), mtar.sum(), mr1.sum()))

regs = json.load(open(B + 'cau_v19/regions_v19.json'))
regions = []
for i, r in enumerate(regs['verd']):
    regions.append(dict(nom='verd_%d' % (i + 1), color='verd', mask=mverd, **{
        k: r[k] for k in ('az_med', 'r_min', 'r_max', 'r_med', 'area_px')}))
for i, r in enumerate(regs['taronja']):
    regions.append(dict(nom='taronja_%d' % (i + 1), color='taronja', mask=mtar, **{
        k: r[k] for k in ('az_med', 'r_min', 'r_max', 'r_med', 'area_px')}))

# ronda 1: components connexos del retall, re-derivats (el json vell te un altre conveni)
ncc, lab, stats, cent = cv2.connectedComponentsWithStats(mr1.astype(np.uint8), 8)
r1regs = []
for k in range(1, ncc):
    if stats[k, cv2.CC_STAT_AREA] < 500:      # 500 px a 1/2 = 2000 px reals
        continue
    sel = lab == k
    rs_, az_ = rr[sel], azz[sel]
    va = np.radians(az_)
    azm = float(np.degrees(np.arctan2(np.sin(va).mean(), np.cos(va).mean())))
    r1regs.append(dict(nom='r1_%d' % len(r1regs), color='ronda1', mask=None,
                       az_med=azm, r_min=float(np.percentile(rs_, 2)),
                       r_max=float(np.percentile(rs_, 98)),
                       r_med=float(np.median(rs_)),
                       area_px=int(sel.sum() * 4), _sel=sel))
r1regs.sort(key=lambda d: -d['area_px'])
for i, d in enumerate(r1regs):
    d['nom'] = 'r1_%d' % (i + 1)
print('ronda 1: %d components >= 2000 px reals' % len(r1regs))
regions += r1regs

G1 = c1h[..., 1]
GF = F[..., 1]
eps = 1e-4

def dif_az(a, b):
    return np.abs(((a - b + 180.0) % 360.0) - 180.0)

def perfil_radial(img, sel, rmin, rmax, pas):
    n = max(2, int(round((rmax - rmin) / pas)))
    bins = np.linspace(rmin, rmax, n + 1)
    idx = np.digitize(rr[sel], bins) - 1
    v = img[sel]
    out = np.full(n, np.nan, np.float32)
    for i in range(n):
        m = idx == i
        if m.sum() >= 20:
            out[i] = np.median(v[m])
    return bins, out

def bony(perf):
    v = perf[np.isfinite(perf)]
    if len(v) < 3:
        return np.nan
    env = np.minimum.accumulate(v)
    return float(np.max(v - env))

def tv_exces(perf):
    v = perf[np.isfinite(perf)]
    if len(v) < 3:
        return np.nan
    d = np.abs(np.diff(v)).sum()
    return float(d - abs(v[-1] - v[0]))

# ---------- 3a + 3b + 3c per regio ----------
res_reg = []
for reg in regions:
    azm = reg['az_med']
    sector = dif_az(azz, azm) < 12.0
    rmin, rmax = reg['r_min'] - 0.5, reg['r_max'] + 0.5
    rmin = max(rmin, 1.2)
    # (a) bony radial
    selp = sector & (rr >= rmin) & (rr <= rmax)
    _, p1 = perfil_radial(G1, selp, rmin, rmax, 0.05)
    _, pF = perfil_radial(GF, selp, rmin, rmax, 0.05)
    b1, bF = bony(p1), bony(pF)
    # (b) TV en exces del croma, r 4..8 pas 0.25 al sector
    selc = sector & (rr >= 4.0) & (rr <= 8.0)
    rg1 = c1h[..., 0] / (c1h[..., 1] + eps)
    bg1 = c1h[..., 2] / (c1h[..., 1] + eps)
    rgF = F[..., 0] / (F[..., 1] + eps)
    bgF = F[..., 2] / (F[..., 1] + eps)
    _, prg1 = perfil_radial(rg1, selc, 4, 8, 0.25)
    _, pbg1 = perfil_radial(bg1, selc, 4, 8, 0.25)
    _, prgF = perfil_radial(rgF, selc, 4, 8, 0.25)
    _, pbgF = perfil_radial(bgF, selc, 4, 8, 0.25)
    tv1 = dict(rg=tv_exces(prg1), bg=tv_exces(pbg1))
    tvF = dict(rg=tv_exces(prgF), bg=tv_exces(pbgF))
    # (c) contrast local aparellat per radi
    if reg.get('mask') is not None:
        selm = reg['mask'] & sector & (rr >= reg['r_min']) & (rr <= reg['r_max'])
    else:
        selm = reg['_sel']
    doff = dif_az(azz, azm)
    selctrl = (doff >= 20.0) & (doff <= 45.0) & ~mtot
    rb = np.arange(reg['r_min'], reg['r_max'] + 1e-6, 0.1)
    dg1, dgF, drg1, drgF, nb = [], [], [], [], 0
    for i in range(len(rb) - 1):
        anell = (rr >= rb[i]) & (rr < rb[i + 1])
        sm = selm & anell
        sc = selctrl & anell
        if sm.sum() < 50 or sc.sum() < 200:
            continue
        nb += 1
        for img, acc in ((G1, dg1), (GF, dgF)):
            gm, gc = np.median(img[sm]), np.median(img[sc])
            acc.append((gm - gc) / max(gc, eps))
        for (num, den), acc in (((c1h[..., 0], c1h[..., 1]), drg1),
                                ((F[..., 0], F[..., 1]), drgF)):
            q = num / (den + eps)
            acc.append(float(np.median(q[sm]) - np.median(q[sc])))
        m_loc = float(np.median(mh[sm]))
    ctr = dict(n_bins=nb,
               dGG_capa1=float(np.median(dg1)) if dg1 else None,
               dGG_F=float(np.median(dgF)) if dgF else None,
               dRG_capa1=float(np.median(drg1)) if drg1 else None,
               dRG_F=float(np.median(drgF)) if drgF else None,
               dGG_capa1_max=float(np.max(np.abs(dg1))) if dg1 else None,
               dGG_F_max=float(np.max(np.abs(dgF))) if dgF else None)
    m_reg = float(np.median(mh[selm])) if selm.sum() else None
    res_reg.append(dict(nom=reg['nom'], color=reg['color'],
                        az_med=round(azm, 1), r_min=reg['r_min'],
                        r_max=reg['r_max'], area_px=reg['area_px'],
                        m_median=m_reg,
                        bony_capa1=b1, bony_F=bF,
                        tv_croma_capa1=tv1, tv_croma_F=tvF,
                        contrast=ctr))
    print('%-10s az %6.1f r %.2f-%.2f m=%.2f  bony %.5f -> %.5f  '
          'tvRG %.4f -> %.4f' % (reg['nom'], azm, reg['r_min'], reg['r_max'],
                                 m_reg if m_reg is not None else -1,
                                 b1, bF, tv1['rg'], tvF['rg']))

# ---------- 3d escombrada global: 24 sectors de 15 graus ----------
rg1 = c1h[..., 0] / (c1h[..., 1] + eps)
rgF = F[..., 0] / (F[..., 1] + eps)
bg1 = c1h[..., 2] / (c1h[..., 1] + eps)
bgF = F[..., 2] / (F[..., 1] + eps)
sectors = []
for k in range(24):
    azc = -180.0 + 7.5 + 15.0 * k
    sect = dif_az(azz, azc) < 7.5
    selp = sect & (rr >= 2.5) & (rr <= 10.0)
    _, p1 = perfil_radial(G1, selp, 2.5, 10.0, 0.05)
    _, pF = perfil_radial(GF, selp, 2.5, 10.0, 0.05)
    selc = sect & (rr >= 4.0) & (rr <= 9.0)
    _, q1 = perfil_radial(rg1, selc, 4, 9, 0.25)
    _, qF = perfil_radial(rgF, selc, 4, 9, 0.25)
    _, u1 = perfil_radial(bg1, selc, 4, 9, 0.25)
    _, uF = perfil_radial(bgF, selc, 4, 9, 0.25)
    sectors.append(dict(az_c=azc, bony_capa1=bony(p1), bony_F=bony(pF),
                        tvRG_capa1=tv_exces(q1), tvRG_F=tv_exces(qF),
                        tvBG_capa1=tv_exces(u1), tvBG_F=tv_exces(uF),
                        m_med=float(np.median(mh[selp]))))
bo1 = np.array([s['bony_capa1'] for s in sectors])
boF = np.array([s['bony_F'] for s in sectors])
print('escombrada: bony capa1 med %.5f max %.5f | F med %.5f max %.5f' %
      (np.nanmedian(bo1), np.nanmax(bo1), np.nanmedian(boF), np.nanmax(boF)))

# ---------- 4b detall tangencial ----------
azbins = np.arange(-180, 180.001, 0.5)
nz = len(azbins) - 1
azidx_all = np.clip(np.digitize(azz, azbins) - 1, 0, nz - 1)
sig_bins = 30  # sigma 15 graus en bins de 0.5

def suau_circ(v, sigma):
    n = len(v)
    k = np.arange(-3 * sigma, 3 * sigma + 1)
    g = np.exp(-0.5 * (k / sigma) ** 2)
    g /= g.sum()
    vv = np.concatenate([v[-3 * sigma:], v, v[:3 * sigma]])
    s = np.convolve(vv, g, 'same')[3 * sigma:3 * sigma + n]
    return s

detall = []
for r0 in np.arange(3.0, 8.0, 0.1):
    an = (rr >= r0) & (rr < r0 + 0.1)
    ai = azidx_all[an]
    v1 = G1[an]; vF = GF[an]; vm = mh[an]
    p1 = np.full(nz, np.nan); pF = np.full(nz, np.nan); pm = np.full(nz, np.nan)
    order = np.argsort(ai)
    ai_s = ai[order]
    v1s, vFs, vms = v1[order], vF[order], vm[order]
    cuts = np.searchsorted(ai_s, np.arange(nz + 1))
    for i in range(nz):
        a, b = cuts[i], cuts[i + 1]
        if b - a >= 5:
            p1[i] = np.median(v1s[a:b])
            pF[i] = np.median(vFs[a:b])
            pm[i] = np.median(vms[a:b])
    ok = np.isfinite(p1) & np.isfinite(pF)
    if ok.sum() < 100:
        continue
    # omple forats per poder suavitzar circularment
    idx = np.arange(nz)
    p1f = np.interp(idx, idx[ok], p1[ok], period=nz)
    pFf = np.interp(idx, idx[ok], pF[ok], period=nz)
    ac1 = (p1f - suau_circ(p1f, sig_bins))[ok]
    acF = (pFf - suau_circ(pFf, sig_bins))[ok]
    cor = float(np.corrcoef(ac1, acF)[0, 1])
    amp = float(np.std(acF) / max(np.std(ac1), 1e-9))
    # nomes zones barrejades (m > 0.8)
    okm = ok & (pm > 0.8)
    corm = ampm = None
    if okm.sum() > 100:
        acm1 = (p1f - suau_circ(p1f, sig_bins))[okm]
        acmF = (pFf - suau_circ(pFf, sig_bins))[okm]
        corm = float(np.corrcoef(acm1, acmF)[0, 1])
        ampm = float(np.std(acmF) / max(np.std(acm1), 1e-9))
    detall.append(dict(r=round(float(r0), 2), corr=cor, amp_ratio=amp,
                       corr_m08=corm, amp_ratio_m08=ampm,
                       ac_rms_capa1=float(np.std(ac1)),
                       m_med=float(np.nanmedian(pm)), n_az=int(ok.sum())))

# ---------- PNG del llenc sencer ----------
def a_png(img_h, cami):
    v = np.clip(img_h[::2, ::2] * 255.0, 0, 255).astype(np.uint8)  # ::4 del real
    cv2.imwrite(cami, v[..., ::-1])

a_png(F, OUT + 'F_compost_pere.png')
a_png(c1h, OUT + 'capa1_original.png')

vis = np.clip(F[::2, ::2] * 255.0, 0, 255).astype(np.uint8)[..., ::-1].copy()
for mmk, col in ((mverd, (0, 255, 0)), (mtar, (0, 165, 255)), (mr1, (0, 0, 255))):
    e = mmk[::2, ::2].astype(np.uint8)
    cont, _ = cv2.findContours(e, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(vis, cont, -1, col, 1)
cv2.imwrite(OUT + 'F_amb_marques.png', vis)

dif = np.abs(GF - G1)[::2, ::2]
dv = np.clip(dif * 255.0 * 10, 0, 255).astype(np.uint8)   # x10 per veure-la
cv2.imwrite(OUT + 'dif_absG_x10.png', dv)

json.dump(dict(geometria=geo, m_mitjana=float(mh.mean()),
               regions=res_reg, escombrada_24=sectors,
               detall_tangencial=detall),
          open(OUT + 'portes_halos_fable5.json', 'w'), indent=1,
          default=lambda o: float(o))
print('FET. json + png a', OUT)

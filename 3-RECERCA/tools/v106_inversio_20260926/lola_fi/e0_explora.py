import json, numpy as np, os
from pathlib import Path
R0 = Path.home()/'Desktop/Eclipse 2026'
LF = R0/'4-RESULTATS/v106_inversio_20260926/limb_frames_sense_llindar'
meta = json.loads((LF/'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF/'numerator.npy', mmap_mode='r'); wt = np.load(LF/'weight.npy', mmap_mode='r'); Dm = np.load(LF/'distance_model.npy', mmap_mode='r')
Rm = meta['radius_model']; hb, wb = by1-by0, bx1-bx0
geo = json.loads((R0/'4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text()); print(geo)
def centre(j):
    D = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(D); iy, ix = hb // 2, wb - 100
    return ix + bx0 - (D[iy, ix] + Rm) * gx[iy, ix], iy + by0 - (D[iy, ix] + Rm) * gy[iy, ix]
yy, xx = np.mgrid[by0:by1, bx0:bx1]
for j in [0,5,13,20,25,26,50,66]:
    W = np.asarray(wt[j]); N = np.asarray(num[j]); D = np.asarray(Dm[j])
    c = centre(j)
    Dh = np.hypot(xx-c[0], yy-c[1]) - Rm
    print(j, fr[j]['exposure'], 'centre', np.round(c,3), 'maxdiff D', float(np.abs(Dh-D).max()), 'frac w>0', [(W[...,k]>0).mean().round(3) for k in range(3)])
    V = np.where(W>0, N/np.maximum(W,1e-30), np.nan)
    for lo,hi in [(-30,-10),(-10,-5),(-5,-2),(-2,0),(0,2),(2,4),(4,8),(8,15),(15,30),(60,100)]:
        m = (D+Rm-452.98-0 >= lo) & (D+Rm-452.98 < hi)
        print('   D', lo, hi, 'medV G', np.nanmedian(V[...,1][m]).round(5), 'w>0', (W[...,1][m]>0).mean().round(3), 'medW', np.median(W[...,1][m]).round(4), 'p90W', np.percentile(W[...,1][m],90).round(4))

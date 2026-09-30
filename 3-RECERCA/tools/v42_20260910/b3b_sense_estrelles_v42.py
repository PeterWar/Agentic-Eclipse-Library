"""B3b (V42) · Base SENSE ESTRELLES per als filtres, i les estrelles com a llum mesurada a part (ordre de Pere: «treu les estrelles dels filtres i deixa-les en una capa de llum mesurada»).
Posicions: els pics reals de l'apuntament A (E1d, 19 estrelles diferents del catàleg HIP/Tycho) refinats a la fusió V42 (suavitzat σ 2, ±10 px, > 4 σ), més els pics cecs
compactes > 7 σ a r > 2,3 R☉ (declarats a part). Substitució, per a cada imatge (fusió, Vixen, Sony corregida) i canal: dins de r_s = 10 px, pla ajustat a l'anell 12–20 px
MÉS els residus de l'anell remostrejats (el gra local es conserva: un pegat llis es veuria als MGN/WOW), amb ploma de 8 a 12 px perquè no quedi cap vora circular. Sortides: cau/{fusion_total,vixen_total,sony_corrected_total}_v42_sense_estrelles.npy,
cau/base_G_v42_sense_estrelles.npy, cau/estrelles_v42.json, vistes (llenç 1/4 amb cercles; galeria abans/després 1:1)."""
from comu42 import *
from scipy.ndimage import gaussian_filter, maximum_filter
RS_ = 10; A0, A1 = 12, 20; rng = np.random.default_rng(42)


def pic_local(img, x, y, rad=10, k=2.0):
    R = rad + 24; s = np.asarray(img[y - R:y + R + 1, x - R:x + R + 1], np.float64)
    if s.shape != (2 * R + 1, 2 * R + 1) or not np.isfinite(s).all(): return None
    g = gaussian_filter(s, k); bg = np.median(g); sd = 1.4826 * np.median(np.abs(g - bg)) + 1e-12; z = (g - bg) / sd
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; zz = np.where(np.hypot(xx, yy) <= rad, z, -np.inf); iy, ix = np.unravel_index(np.argmax(zz), zz.shape)
    return dict(dx=int(ix - R), dy=int(iy - R), snr=float(zz[iy, ix]))


def treu(arr, x, y, m):
    """substitueix el disc r ≤ RS_ a (x, y) per: pla local (ajustat a l'anell 12–20) + el GRA d'un pegat veí de la mateixa imatge (desplaçat DESP px, menys el seu propi pla),
    perquè el gra substituït tingui la mateixa textura correlacionada que el del voltant (un pegat de soroll blanc es veia als MGN/WOW). Només si anell i pegat són dins del suport."""
    R = A1 + 1; y0, y1, x0, x1 = y - R, y + R + 1, x - R, x + R + 1
    if y0 < 0 or x0 < 0 or y1 > H or x1 > W or not m[y0:y1, x0:x1].all(): return False
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; rr = np.hypot(xx, yy); an = (rr >= A0) & (rr <= A1); disc = rr <= RS_ + 2; wf = np.clip((RS_ + 2 - rr) / 4.0, 0, 1)[disc]   # ploma: pes del farcit 1 fins a r 8, 0 a r 12
    A = np.c_[np.ones(an.sum()), xx[an], yy[an]]
    src = None
    for dxp, dyp in ((32, 0), (-32, 0), (0, 32), (0, -32), (24, 24), (-24, -24)):
        sy0, sy1, sx0, sx1 = y0 + dyp, y1 + dyp, x0 + dxp, x1 + dxp
        if sy0 >= 0 and sx0 >= 0 and sy1 <= H and sx1 <= W and m[sy0:sy1, sx0:sx1].all(): src = (sy0, sy1, sx0, sx1); break
    if src is None: return False
    sub = np.asarray(arr[y0:y1, x0:x1]); psub = np.asarray(arr[src[0]:src[1], src[2]:src[3]])
    for c in range(sub.shape[2] if sub.ndim == 3 else 1):
        ch = sub[..., c] if sub.ndim == 3 else sub; pc = psub[..., c] if psub.ndim == 3 else psub
        v = ch[an]; ok = np.isfinite(v); coef = np.linalg.lstsq(A[ok], v[ok], rcond=None)[0]; plane = coef[0] + coef[1] * xx + coef[2] * yy
        vp = pc[an]; okp = np.isfinite(vp); coefp = np.linalg.lstsq(A[okp], vp[okp], rcond=None)[0]; planep = coefp[0] + coefp[1] * xx + coefp[2] * yy
        fill = plane[disc] + (pc[disc] - planep[disc]); fill = np.where(np.isfinite(fill), fill, plane[disc]); ch[disc] = (wf * fill + (1 - wf) * ch[disc]).astype(ch.dtype)
        if sub.ndim == 3: sub[..., c] = ch
        else: sub[:] = ch
    arr[y0:y1, x0:x1] = sub; return True


def main():
    r, t = coords(); rows = json.loads((REB41 / 'E1d_estrelles_dobles.json').read_text())['files']
    F = np.load(CAU42 / 'fusion_total_v42.npy', mmap_mode='r'); m = np.load(CAU42 / 'support_v42.npy')
    seeds = []
    for d in rows:
        if d.get('sonyA') and d['sonyA'][0]['snr'] > 4: seeds.append((d['cat_x'] + d['sonyA'][0]['dx'], d['cat_y'] + d['sonyA'][0]['dy'], 'A'))
        elif d.get('fusio') and d['fusio'][0]['snr'] > 4: seeds.append((d['cat_x'] + d['fusio'][0]['dx'], d['cat_y'] + d['fusio'][0]['dy'], 'F'))
    G = F[..., 1]; stars = []
    for x, y, src in seeds:
        p = pic_local(G, int(x), int(y))
        if p is None or p['snr'] < 4: continue
        X, Y = int(x) + p['dx'], int(y) + p['dy']
        if any(np.hypot(X - s['x'], Y - s['y']) < 8 for s in stars): continue
        stars.append(dict(x=X, y=Y, r_R=float(r[Y, X] / RS), snr=p['snr'], origen='cataleg'))
    # pics cecs compactes > 7 σ a r > 2,3 R☉ (a 1/2 de resolució per anar de pressa; després refinats)
    g2 = np.asarray(G[::2, ::2], np.float32); ok2 = m[::2, ::2] & (r[::2, ::2] > 2.3 * RS); sm = gaussian_filter(np.where(ok2, g2, 0), 1.0); bg = gaussian_filter(np.where(ok2, g2, 0), 12); wt = gaussian_filter(ok2.astype(np.float32), 12)
    z = np.where(wt > 0.9, (sm - bg / np.maximum(wt, 1e-6)), 0); sd = 1.4826 * np.median(np.abs(z[ok2 & (wt > 0.9)])) + 1e-12; z /= sd
    pk = (z == maximum_filter(z, 9)) & (z > 7) & ok2; ys, xs = np.nonzero(pk); n_cec = 0
    for yy_, xx_ in zip(ys, xs):
        X, Y = int(xx_ * 2), int(yy_ * 2); p = pic_local(G, X, Y, rad=4)
        if p is None or p['snr'] < 7: continue
        X, Y = X + p['dx'], Y + p['dy']
        if any(np.hypot(X - s['x'], Y - s['y']) < 12 for s in stars): continue
        stars.append(dict(x=X, y=Y, r_R=float(r[Y, X] / RS), snr=p['snr'], origen='cec')); n_cec += 1
    log(f'{len(stars)} estrelles a treure: {len(stars) - n_cec} del catàleg + {n_cec} cegues > 7 σ')
    outs = {'fusion_total': CAU42 / 'fusion_total_v42.npy', 'vixen_total': CAU38 / 'vixen_total_v38.npy', 'sony_corrected_total': CAU42 / 'sony_corrected_total_v42.npy'}
    for nom, src in outs.items():
        a = np.array(np.load(src, mmap_mode='r')); ms = np.all(np.isfinite(a) & (a > 0), axis=2); n = 0
        for s in stars: n += treu(a, s['x'], s['y'], ms)
        np.save(CAU42 / f'{nom}_v42_sense_estrelles.npy', a); log(f'{nom}: {n} estrelles substituïdes'); 
        if nom == 'fusion_total': base = a[..., 1].copy(); base[~m] = 0; np.save(CAU42 / 'base_G_v42_sense_estrelles.npy', base)
        del a
    savejson(CAU42 / 'estrelles_v42.json', dict(radi_px=RS_, anell_px=[A0, A1], estrelles=stars)); savejson(REB42 / 'B3b_sense_estrelles.json', dict(n=len(stars), n_cec=n_cec, estrelles=stars))
    # vistes: llenç 1/4 amb cercles; galeria 1:1 abans/després (fusió) de les 12 més fortes
    Fs = np.load(CAU42 / 'fusion_total_v42_sense_estrelles.npy', mmap_mode='r'); lg = np.log(np.maximum(np.asarray(G[::4, ::4], np.float32), 1)); lo, hi = np.percentile(lg[m[::4, ::4]], [1, 99.7])
    img = cv2.cvtColor((np.clip((lg - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    for s in stars: cv2.circle(img, (s['x'] // 4, s['y'] // 4), 10, (0, 255, 0) if s['origen'] == 'cataleg' else (0, 200, 255), 1)
    cv2.imwrite(str(VIS42 / 'B3b_estrelles_llenc_quart.png'), img)
    g = sorted(stars, key=lambda s: -s['snr'])[:12]; T = 49; Z = 4; can = np.full((len(g) * (T * Z + 6) + 30, 2 * (T * Z + 6) + 240, 3), 25, np.uint8)
    for i, s in enumerate(g):
        for j, arr in enumerate((G, Fs[..., 1])):
            sub = np.asarray(arr[s['y'] - 24:s['y'] + 25, s['x'] - 24:s['x'] + 25], np.float64); bg = np.median(sub); sd = 1.4826 * np.median(np.abs(sub - bg)) + 1e-9
            tile = cv2.resize((np.clip(((sub - bg) / sd / 5 + 1) / 2, 0, 1) * 255).astype(np.uint8), (T * Z, T * Z), interpolation=cv2.INTER_NEAREST); y0, x0 = 30 + i * (T * Z + 6), 240 + j * (T * Z + 6); can[y0:y0 + T * Z, x0:x0 + T * Z] = tile[..., None]
        cv2.putText(can, f"({s['x']},{s['y']}) {s['r_R']:.1f}R {s['snr']:.0f}s {s['origen']}", (4, 30 + i * (T * Z + 6) + T * Z // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 255, 200), 1)
    cv2.putText(can, 'fusio V42 (+-5 sigma)  |  sense estrelles', (240, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1); cv2.imwrite(str(VIS42 / 'B3b_galeria_abans_despres.png'), can); log('B3b fet')


if __name__ == '__main__':
    main()

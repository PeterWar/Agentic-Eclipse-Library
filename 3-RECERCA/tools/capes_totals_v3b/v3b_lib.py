"""Biblioteca de CapesTotalsV3b: màscares radials × porta lunar per capa × protecció P3/P4, composició Normal en espai
codificat, porta de costura recalibrada (research/87 §9.4) i pilots 1:1. Coordenades de LLENÇ (7648x5353) llevat que es digui."""
import json, hashlib, numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from geom import V2B, V3B, OFF, W as FW, H as FH, SUN as SUN_LOCAL, R_SUN, ELL, R_moon, member_centres, smootherstep
CW, CH = 7648, 5353
FRAME = (OFF[0], OFF[1], OFF[0]+FW, OFF[1]+FH)   # left, top, right, bottom
SUN = (SUN_LOCAL[0]+OFF[0], SUN_LOCAL[1]+OFF[1])  # (4020.89, 2737.66)
MOON7_C2 = (4033.62, 2735.62, 451.34)            # MOON[7] de build_corretgint2 (llenç; ID7 no s'ha mogut a V2b)
ID7_CORE, ID7_FEATHER = 3.0, 18.0
BAND_R = 460.0 + 4.0 + 14.0                        # 478 px: final de la transició de 14 px de l'apilador
LAYER_IDS = (8, 9, 10)

def sha256_u16(a):
    return hashlib.sha256(np.ascontiguousarray(a).astype('>u2').tobytes()).hexdigest()

def canvas_grid():
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32); return xx, yy

def r_sun_canvas(xx, yy):
    return np.hypot(xx-SUN[0], yy-SUN[1])/np.float32(R_SUN)

def moon_centre_canvas(i):
    e = ELL[str(i)]; return (e['cx']+OFF[0], e['cy']+OFF[1])

def d_moon_canvas(i, xx, yy):
    """Distància el·líptica equivalent (px) al centre lunar de la capa i, en coordenades de llenç."""
    e = ELL[str(i)]; cx, cy = e['cx']+OFF[0], e['cy']+OFF[1]
    a, b, th = e['a'], e['b'], np.radians(e['theta_deg'])
    dx, dy = xx-cx, yy-cy; c, s = np.cos(th), np.sin(th)
    u = dx*c + dy*s; v = -dx*s + dy*c
    return np.sqrt((u/a)**2 + (v/b)**2) * np.float32(np.sqrt(a*b))

def band_gate(i, xx, yy, feather_px=20.0):
    """Porta lunar de la capa i: zero on qualsevol membre de l'apilat té el seu disc (+marge+transició = 478 px),
    ploma radial smootherstep de `feather_px` cap enfora. Geometria pura: centres = referència + v·Δt."""
    ref, cs = member_centres(i)
    dmin = None
    for f, (cx, cy, dt) in cs.items():
        d = np.hypot(xx-(cx+OFF[0]), yy-(cy+OFF[1]))
        dmin = d if dmin is None else np.minimum(dmin, d)
    g = smootherstep((dmin - BAND_R)/feather_px).astype(np.float32)
    return g, dmin

def load_layer_rgb(i):
    """RGB u16 del ràster de la capa (6960x4640, coordenades locals)."""
    R_ = np.load(f'{V3B}/src_id{i}_R.npy', mmap_mode='r'); G_ = np.load(f'{V2B}/src_id{i}_G.npy', mmap_mode='r'); B_ = np.load(f'{V3B}/src_id{i}_B.npy', mmap_mode='r')
    return R_, G_, B_

def load_abans_rgb():
    """Compost V2b (ID3/4/5/7) en float32 0..1, canals RGB, llenç sencer."""
    m = np.load(f'{V2B}/work/merged_rgba16.npy', mmap_mode='r')
    return m

def compose(abans_rgb_f32, i, alpha_canvas):
    """DESPRÉS = ABANS·(1-α) + capa·α dins del marc de la capa; fora, idèntic. Retorna float32 (CH,CW,3)."""
    out = np.array(abans_rgb_f32, dtype=np.float32, copy=True)
    l, t, r, b = FRAME
    a = alpha_canvas[t:b, l:r].astype(np.float32)/65535.
    for k, ch in enumerate(load_layer_rgb(i)):
        src = np.asarray(ch, np.float32)/65535.
        out[t:b, l:r, k] = out[t:b, l:r, k]*(1-a) + src*a
    return out

def quantize(f):
    return np.clip(np.floor(np.asarray(f, np.float64)*65535.0+0.5), 0, 65535).astype(np.uint16)

def lum(rgb):
    return (np.asarray(rgb[..., 0], np.float32)+np.asarray(rgb[..., 1], np.float32)+np.asarray(rgb[..., 2], np.float32))/3.0

# ---------- protecció P3/P4 derivada de la màscara d'ID7 de Corretgint2 ----------
def protection_factor(xx, yy):
    """PF = màscara7 / (perfil radial solar de la màscara7 × porta lunar analítica d'ID7), retallat a [0,1].
    Val 1 on la màscara d'ID7 és purament radial×lunar, i <1 (fins a 0) a P3, P4, h125 i nuclis cremats."""
    m7 = np.load(f'{V3B}/src_id7_mask.npy', mmap_mode='r')
    m7 = np.asarray(m7, np.float32)/65535.
    d7 = np.hypot(xx-MOON7_C2[0], yy-MOON7_C2[1])
    g7 = smootherstep((d7-(MOON7_C2[2]+ID7_CORE))/ID7_FEATHER).astype(np.float32)
    r = r_sun_canvas(xx, yy)
    l, t, rr_, b = FRAME
    sel = np.zeros((CH, CW), bool); sel[t:b, l:rr_] = True
    ok = sel & (g7 > 0.999)
    bins = np.arange(0.95, 12.0, 0.002); idx = np.digitize(r, bins)-1
    prof = np.zeros(len(bins), np.float32)
    cnt = np.bincount(idx[ok].ravel(), minlength=len(bins)+1)[:len(bins)]
    # mediana per anell (robusta als zeros de protecció): ho fem per trossos amb percentil
    for k in np.nonzero(cnt > 50)[0]:
        pass
    # implementació vectorial de la mediana per anell: ordenem per anell
    flat_idx = idx[ok].ravel(); flat_val = m7[ok].ravel()
    order = np.argsort(flat_idx, kind='stable'); flat_idx = flat_idx[order]; flat_val = flat_val[order]
    starts = np.searchsorted(flat_idx, np.arange(len(bins))); ends = np.searchsorted(flat_idx, np.arange(len(bins))+1)
    for k in range(len(bins)):
        if ends[k]-starts[k] > 50: prof[k] = np.median(flat_val[starts[k]:ends[k]])
    # fora del rang mesurat: extrapola constant
    good = np.nonzero(cnt > 50)[0]
    prof[:good[0]] = prof[good[0]]; prof[good[-1]+1:] = prof[good[-1]]
    prof_img = prof[np.clip(idx, 0, len(bins)-1)]
    den = prof_img*g7
    pf = np.ones((CH, CW), np.float32)
    m = den > 0.02
    pf[m] = np.clip(m7[m]/den[m], 0, 1)
    # on la porta lunar d'ID7 o el perfil són ~0 no hi ha informació: PF=1 (les nostres portes ja hi són 0)
    return pf, dict(prof_bins=bins.tolist(), prof=prof.tolist())

# ---------- perfils i porta ----------
def ring_medians(img, rad, r0, r1, step, sel=None, sectors=None, az=None):
    """Mediana per anell [r0,r1) de pas `step` sobre `rad` (px o R☉). Retorna (centres, global, per_sector[nsec, nbins])."""
    bins = np.arange(r0, r1+step*0.5, step); nb = len(bins)-1
    m = (rad >= r0) & (rad < bins[-1])
    if sel is not None: m &= sel
    idx = np.digitize(rad[m], bins)-1; v = img[m]
    g = np.full(nb, np.nan, np.float32)
    order = np.argsort(idx, kind='stable'); idx = idx[order]; v = v[order]
    st = np.searchsorted(idx, np.arange(nb)); en = np.searchsorted(idx, np.arange(nb)+1)
    for k in range(nb):
        if en[k]-st[k] >= 30: g[k] = np.median(v[st[k]:en[k]])
    S = None
    if sectors:
        a = az[m][order]; S = np.full((sectors, nb), np.nan, np.float32)
        sidx = np.floor(a/(360.0/sectors)).astype(int) % sectors
        key = idx*sectors + sidx; o2 = np.argsort(key, kind='stable'); key = key[o2]; v2 = v[o2]
        st2 = np.searchsorted(key, np.arange(nb*sectors)); en2 = np.searchsorted(key, np.arange(nb*sectors)+1)
        for kk in range(nb*sectors):
            if en2[kk]-st2[kk] >= 30: S[kk % sectors, kk//sectors] = np.median(v2[st2[kk]:en2[kk]])
    return 0.5*(bins[:-1]+bins[1:]), g, S

def _peaks(profile_ok, ok):
    f = np.interp(np.arange(len(profile_ok)), np.nonzero(ok)[0], profile_ok[ok])
    f = ndi.gaussian_filter1d(f, 1.0, mode='nearest')
    pk, pr = find_peaks(-f, prominence=0, width=1)
    return f, pk, pr

def minima_report(centres, before, after, step_px, name, layer=None, min_width_px=10.0, min_rel=0.01, nsigma=3.0, r_max_defecte=1e9):
    """Mínims del perfil DESPRÉS que no són ni a ABANS ni a la CAPA sola (a ±max(3 bins, amplada/2)): són els que crea la
    costura. Defecte si prominència ≥1 % del nivell I ≥ nσ de la dispersió del perfil I amplada ≥ min_width_px."""
    out = []
    ok = np.isfinite(after) & np.isfinite(before)
    if layer is not None: ok &= np.isfinite(layer)
    if ok.sum() < 20: return out, None
    af, pk, props = _peaks(after, ok)
    sm = ndi.gaussian_filter1d(af, 6, mode='nearest'); resid = (af-sm)/np.maximum(sm, 1e-6)
    sigma = 1.4826*np.median(np.abs(resid[ok]))
    _, pk_b, pr_b = _peaks(before, ok)
    pk_l = np.array([], int); pr_l = None
    if layer is not None: _, pk_l, pr_l = _peaks(layer, ok)
    for j, p in enumerate(pk):
        if not ok[p]: continue
        prom = props['prominences'][j]; wbins = props['widths'][j]; width = wbins*step_px
        rel = prom/max(af[p], 1e-6)
        tol = max(3, int(wbins/4)+1)
        # present a una font si hi ha un mínim a ±tol amb prominència ABSOLUTA ≥ 1/2 de la del compost
        def present(pks, prs):
            if len(pks) == 0: return False
            near = np.abs(pks-p) <= tol
            return bool(np.any(near & (prs['prominences'] >= prom/2.0)))
        nou = not present(pk_b, pr_b) and not (layer is not None and present(pk_l, pr_l))
        dins_finestra = (centres[p] <= r_max_defecte)
        defecte = nou and dins_finestra and rel >= min_rel and rel >= nsigma*sigma and width >= min_width_px
        if (nou and rel >= 0.003) or defecte:
            out.append(dict(perfil=name, r=round(float(centres[p]), 3), prominencia_DN=round(float(prom*65535), 1), prominencia_pct=round(float(100*rel), 3),
                            amplada_px=round(float(width), 1), n_sigma=round(float(rel/max(sigma, 1e-9)), 1), nou=bool(nou), defecte=bool(defecte)))
    return out, float(sigma)

def gate(abans_f, despres_f, alpha_canvas, i, pf, xx, yy, out_json, extra=None, layer_lum=None):
    """Porta recalibrada sobre el compost DESPRÉS. Retorna dict amb tots els números i el veredicte."""
    La = lum(abans_f); Ld = lum(despres_f)
    l, t, r_, b = FRAME
    res = dict(layer=i, minims=[], sigmes={})
    # (1) perfils lunar-cèntrics fins a 1,2 R☉ (535 px) en px, pas 2 px; 24 sectors
    cx, cy = moon_centre_canvas(i); Rm = R_moon(i)
    dmo = np.hypot(xx-cx, yy-cy); azm = np.degrees(np.arctan2(-(yy-cy), xx-cx)) % 360
    sel = np.zeros((CH, CW), bool); sel[t:b, l:r_] = True
    cL, gA, SA = ring_medians(La, dmo, Rm+2, 1.2*R_SUN+Rm-R_SUN+60, 2.0, sel, 24, azm)
    _, gD, SD = ring_medians(Ld, dmo, Rm+2, 1.2*R_SUN+Rm-R_SUN+60, 2.0, sel, 24, azm)
    _, gL, SL = ring_medians(layer_lum, dmo, Rm+2, 1.2*R_SUN+Rm-R_SUN+60, 2.0, sel, 24, azm)
    mins, sg = minima_report(cL, gA, gD, 2.0, 'lunar_global', gL); res['minims'] += mins; res['sigmes']['lunar_global'] = sg
    for s in range(24):
        mins, sg = minima_report(cL, SA[s], SD[s], 2.0, f'lunar_sector_{s*15:03d}', SL[s]); res['minims'] += mins
    # (2) perfils solar-cèntrics 1,0–4,6 R☉, pas 0,005 R☉ (2,2 px), global i 24 sectors
    rs = r_sun_canvas(xx, yy); azs = np.degrees(np.arctan2(-(yy-SUN[1]), xx-SUN[0])) % 360
    cS, gA2, SA2 = ring_medians(La, rs, 1.0, 4.6, 0.005, sel, 24, azs)
    _, gD2, SD2 = ring_medians(Ld, rs, 1.0, 4.6, 0.005, sel, 24, azs)
    _, gL2, SL2 = ring_medians(layer_lum, rs, 1.0, 4.6, 0.005, sel, 24, azs)
    mins, sg = minima_report(cS, gA2, gD2, 0.005*R_SUN, 'solar_global', gL2, r_max_defecte=3.0); res['minims'] += mins; res['sigmes']['solar_global'] = sg
    for s in range(24):
        mins, sg = minima_report(cS, SA2[s], SD2[s], 0.005*R_SUN, f'solar_sector_{s*15:03d}', SL2[s], r_max_defecte=3.0); res['minims'] += mins
    res['n_minims_defecte'] = int(sum(m['defecte'] for m in res['minims']))
    res['n_minims_nous_reportats'] = int(sum(m['nou'] for m in res['minims']))
    res['perfils'] = dict(lunar=dict(r_px=cL.tolist(), abans=np.nan_to_num(gA, nan=-1).tolist(), despres=np.nan_to_num(gD, nan=-1).tolist(), capa=np.nan_to_num(gL, nan=-1).tolist()),
                          solar=dict(r_rsun=cS.tolist(), abans=np.nan_to_num(gA2, nan=-1).tolist(), despres=np.nan_to_num(gD2, nan=-1).tolist(), capa=np.nan_to_num(gL2, nan=-1).tolist()))
    # criteri V1 (qa_ct1): perfil lunar-cèntric global del DESPRÉS sense cap mínim local entre R+16 i 708 px (1 px, suavitzat lleu)
    c1, g1, _ = ring_medians(Ld, dmo, Rm+16, 708, 1.0, sel)
    g1s = ndi.gaussian_filter1d(np.interp(np.arange(len(g1)), np.nonzero(np.isfinite(g1))[0], g1[np.isfinite(g1)]), 2)
    pk1, pr1 = find_peaks(-g1s, prominence=0.001*np.nanmedian(g1s))
    res['V1_minims_locals_lunar'] = [dict(r_px=round(float(c1[p]), 1), prominencia_pct=round(float(100*pr1['prominences'][j]/g1s[p]), 3)) for j, p in enumerate(pk1)]
    # (3) empremta no radial: compost amb la màscara promitjada per anell solar (dins del marc), 1,0–3,0 R☉, fora de nuclis i zona lunar
    a = alpha_canvas.astype(np.float32)/65535.
    ca, pa, _ = ring_medians(a, rs, 0.98, 12.0, 0.005, sel)
    pa = np.nan_to_num(pa, nan=0.0)
    idx = np.clip(np.digitize(rs, np.arange(0.98, 12.0+0.0025, 0.005))-1, 0, len(pa)-1)
    a_rad = pa[idx].astype(np.float32); a_rad[~sel] = 0
    # compost amb la màscara radial (mitjana per anell de la pròpia màscara: inclou l'efecte mitjà de la porta lunar)
    d_rad = compose(abans_f, i, quantize(a_rad))
    Lr = lum(d_rad)
    zona = sel & (rs >= 1.0) & (rs <= 3.0) & (pf > 0.999) & (dmo > Rm+80)
    rel = (Ld[zona]-Lr[zona])/np.maximum(Lr[zona], 1e-4)
    res['empremta_no_radial_rms_pct'] = round(float(100*np.sqrt(np.mean(rel**2))), 4)
    zona2 = sel & (rs >= 1.0) & (rs <= 3.0)
    rel2 = (Ld[zona2]-Lr[zona2])/np.maximum(Lr[zona2], 1e-4)
    res['empremta_no_radial_rms_pct_inclou_portes'] = round(float(100*np.sqrt(np.mean(rel2**2))), 4)
    del d_rad, Lr
    # (4) nuclis P3/P4 (PF<1 dins 400-600 px de la Lluna de Corretgint2) i discs lunars: diferència exacta zero
    Qa = quantize(abans_f); Qd = quantize(despres_f)
    d7 = np.hypot(xx-MOON7_C2[0], yy-MOON7_C2[1])
    nuclis = (pf < 0.999) & (d7 >= 380) & (d7 <= 620)
    m7 = np.asarray(np.load(f'{V3B}/src_id7_mask.npy', mmap_mode='r'))
    zeros7 = (m7 == 0) & (d7 > MOON7_C2[2]+ID7_CORE+ID7_FEATHER+2) & (d7 <= 620) & sel  # zeros d'ID7 fora de la seva porta lunar: P3/P4/hot
    res['nuclis_P3P4_px'] = int(zeros7.sum())
    res['nuclis_P3P4_dif_max_DN'] = int(np.abs(Qd[zeros7].astype(np.int32)-Qa[zeros7].astype(np.int32)).max()) if zeros7.any() else 0
    res['nuclis_P3P4_alpha_max'] = int(alpha_canvas[zeros7].max()) if zeros7.any() else 0
    discs = {}
    for j in (3, 4, 5, 7, 8, 9, 10):
        if j in (8, 9, 10):
            dj = d_moon_canvas(j, xx, yy); Rj = R_moon(j)
        else:
            from geom import ELL as _E
            mm = {3: (4036.27+2, 2740.24-2, 451.83), 4: (4036.494-1, 2738.531-1, 451.800), 5: (4037.03-1, 2738.18-1, 451.71), 7: MOON7_C2}[j]
            dj = np.hypot(xx-mm[0], yy-mm[1]); Rj = mm[2]
        zz = dj <= Rj + 2
        discs[str(j)] = dict(px=int(zz.sum()), alpha_max=int(alpha_canvas[zz].max()), dif_max_DN=int(np.abs(Qd[zz].astype(np.int32)-Qa[zz].astype(np.int32)).max()))
    res['discs_lunars'] = discs
    # (5) fora del suport de la màscara: byte-idèntic
    fora = alpha_canvas == 0
    res['fora_suport_dif_max_DN'] = int(np.abs(Qd[fora].astype(np.int32)-Qa[fora].astype(np.int32)).max())
    res['suport_px'] = int((~fora).sum())
    if extra: res.update(extra)
    ok = (res['n_minims_defecte'] == 0 and res['empremta_no_radial_rms_pct'] <= 0.5 and res['nuclis_P3P4_dif_max_DN'] == 0 and res['fora_suport_dif_max_DN'] == 0
          and all(v['dif_max_DN'] == 0 for v in discs.values()) and len(res['V1_minims_locals_lunar']) == 0)
    res['veredicte'] = 'ACCEPTADA' if ok else 'REBUTJADA'
    json.dump(res, open(out_json, 'w'), indent=1)
    return res, Qa, Qd

# ---------- pilots 1:1 ----------
def _stretch(a, lo, hi, gamma=0.5):
    return np.clip((a-lo)/max(hi-lo, 1e-6), 0, 1)**gamma

def pilot_crop(abans_f, despres_f, layer_rgb_canvas_getter, alpha_canvas, cx, cy, path, size=1024, title=''):
    from PIL import Image, ImageDraw
    x0 = int(np.clip(cx-size//2, 0, CW-size)); y0 = int(np.clip(cy-size//2, 0, CH-size))
    A = np.asarray(abans_f[y0:y0+size, x0:x0+size]); D = np.asarray(despres_f[y0:y0+size, x0:x0+size])
    C = layer_rgb_canvas_getter(y0, y0+size, x0, x0+size)
    M = alpha_canvas[y0:y0+size, x0:x0+size].astype(np.float32)/65535.
    lo, hi = np.percentile(lum(A), [0.5, 99.5])
    views = [_stretch(A, lo, hi), _stretch(C, lo, hi), np.repeat(M[..., None], 3, axis=2), _stretch(D, lo, hi)]
    dif = (lum(D)-lum(A))/np.maximum(lum(A), 1e-3)
    ev = np.log2(np.maximum(lum(D), 1e-4)/np.maximum(lum(A), 1e-4))
    dv = np.clip(ev/3.0+0.5, 0, 1); views.append(np.repeat(dv[..., None], 3, axis=2))
    panel = np.concatenate(views, axis=1)
    im = Image.fromarray((panel*255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    for k, lab in enumerate(['inferior (ABANS)', 'candidata (capa)', 'màscara', 'resultat (DESPRÉS)', 'diferència: log2(després/abans) ±1,5 EV']):
        dr.text((k*size+8, 8), lab, fill=(255, 80, 80)); 
    dr.text((8, size-20), f'{title} retall llenç x={x0}..{x0+size} y={y0}..{y0+size}, estirament {lo:.4f}-{hi:.4f} γ0,5', fill=(255, 80, 80))
    im.save(path)
    return dict(path=path, x0=x0, y0=y0, lo=float(lo), hi=float(hi), dif_rel_med_pct=round(float(100*np.median(dif[M > 0.01])) if (M > 0.01).any() else 0.0, 3))

def overview(despres_f, path, scale=4):
    from PIL import Image
    D = np.asarray(despres_f[::scale, ::scale]); L = lum(D)
    lo, hi = np.percentile(L, [0.5, 99.8])
    img = np.clip((D-lo)/(hi-lo), 0, 1)**0.35
    Image.fromarray((img*255).astype(np.uint8)).save(path)


def created_rises(centres, pa, pl, w, floor_l, sigma_bins=3):
    """Trams on el compost (1-w)·A + w·L PUJA amb r mentre A i L baixen (suavitzats σ bins): amplitud relativa màxima
    d'una pujada creada, només on L ≥ 3× el seu terra."""
    ok = np.isfinite(pa) & np.isfinite(pl)
    if ok.sum() < 20: return 0.0
    x = np.arange(len(pa))
    A = ndi.gaussian_filter1d(np.interp(x, x[ok], pa[ok]), sigma_bins, mode='nearest')
    L = ndi.gaussian_filter1d(np.interp(x, x[ok], pl[ok]), sigma_bins, mode='nearest')
    C = (1-w)*A + w*L
    dA, dL, dC = np.gradient(A), np.gradient(L), np.gradient(C)
    bad = (dC > 0) & (dA <= 0) & (dL <= 0) & (L >= 3*floor_l) & ok
    worst = 0.0; run = 0.0; lvl = None
    for k in range(len(C)):
        if bad[k]:
            run += dC[k]; lvl = C[k] if lvl is None else lvl
        else:
            if lvl is not None: worst = max(worst, run/max(lvl, 1e-6))
            run = 0.0; lvl = None
    if lvl is not None: worst = max(worst, run/max(lvl, 1e-6))
    return float(worst)


RAMPA_SIGMA_RSUN = 0.05   # suavitzat de la rampa lineal (22 px): treu els dos colzes sense apujar el pendent central

def rampa(r, r_a, r_b, sig=RAMPA_SIGMA_RSUN):
    """Rampa radial lineal r_a→r_b convolucionada amb una gaussiana σ (forma tancada). Pendent central 1/(r_b-r_a),
    contra 1,875/(r_b-r_a) de l'smootherstep, que és el que creava pujades al compost (research/87 §11.2)."""
    from scipy.special import erf
    def F(x):
        z = x/sig; return x*0.5*(1+erf(z/np.sqrt(2))) + sig*np.exp(-0.5*z*z)/np.sqrt(2*np.pi)
    return np.clip((F(r-r_a) - F(r-r_b))/(r_b-r_a), 0, 1).astype(np.float32)

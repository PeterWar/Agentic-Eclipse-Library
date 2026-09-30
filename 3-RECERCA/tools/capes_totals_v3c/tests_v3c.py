"""Tests de V3c: (1) porta de costura (mínims nous lunar/solar global+24 sectors, criteri V1, empremta no radial incloent la
zona lunar, nuclis P3/P4 i discs byte-idèntics, fora del suport byte-idèntic); (2) cobertura de validesa per cel·la;
(3) test ABSOLUT per sectors (5°) lunar-cèntric; (4) pilots de baix a dalt."""
import numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from v3c_lib import *
ell = json.load(open(f'{SCR}/lluna_ellipse_llenc.json')); rang = json.load(open(f'{SCR}/rang.json'))
P3 = np.load(f'{SCR}/masks/P3.npy', mmap_mode='r'); P4 = np.load(f'{SCR}/masks/P4.npy', mmap_mode='r')
PROT = (np.asarray(P3) > 0) | (np.asarray(P4) > 0)
PCORE = (np.asarray(P3) >= 1) | (np.asarray(P4) >= 1)
XX, YY = canvas_grid(); RS = r_sun(XX, YY); AZS = az_sun(XX, YY)
SEL = frame_sel(7)
def lunar_coords(i):
    e = ell[str(i)]; d = d_moon(e, XX, YY); az = np.degrees(np.arctan2(-(YY-e['cy']), XX-e['cx'])) % 360
    return d, az, R_eq(e)
def r_valid_outer(i, snr=5.0):
    return max([r['r'] for r in rang[str(i)] if r['snr'] >= snr] or [0.0]) if str(i) in rang else 99.0

def porta(abans_f, despres_f, alpha_u16, i, layer_lum, gate_f32, out_json, extra=None):
    """Porta de costura V3b recalibrada, amb l'empremta no radial calculada des de R+3 (exclou només P3/P4 amb ploma)."""
    La = lum(abans_f); Ld = lum(despres_f)
    res = dict(layer=i, minims=[], sigmes={})
    d, azm, Rm = lunar_coords(i)
    cL, gA, SA = ring_medians(La, d, Rm+2, Rm+2+0.3*R_SUN+60, 2.0, SEL, 24, azm)
    _, gD, SD = ring_medians(Ld, d, Rm+2, Rm+2+0.3*R_SUN+60, 2.0, SEL, 24, azm)
    _, gL, SL = ring_medians(layer_lum, d, Rm+2, Rm+2+0.3*R_SUN+60, 2.0, SEL, 24, azm)
    m, sg = minima_report(cL, gA, gD, 2.0, 'lunar_global', gL); res['minims'] += m; res['sigmes']['lunar_global'] = sg
    for s in range(24):
        m, sg = minima_report(cL, SA[s], SD[s], 2.0, f'lunar_sector_{s*15:03d}', SL[s]); res['minims'] += m
    cS, gA2, SA2 = ring_medians(La, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    _, gD2, SD2 = ring_medians(Ld, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    _, gL2, SL2 = ring_medians(layer_lum, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    m, sg = minima_report(cS, gA2, gD2, 0.005*R_SUN, 'solar_global', gL2, r_max_defecte=3.0); res['minims'] += m; res['sigmes']['solar_global'] = sg
    for s in range(24):
        m, sg = minima_report(cS, SA2[s], SD2[s], 0.005*R_SUN, f'solar_sector_{s*15:03d}', SL2[s], r_max_defecte=3.0); res['minims'] += m
    res['n_minims_defecte'] = int(sum(x['defecte'] for x in res['minims'])); res['n_minims_nous_reportats'] = int(sum(x['nou'] for x in res['minims']))
    res['perfils'] = dict(lunar=dict(r_px=cL.tolist(), abans=np.nan_to_num(gA, nan=-1).tolist(), despres=np.nan_to_num(gD, nan=-1).tolist(), capa=np.nan_to_num(gL, nan=-1).tolist()),
                          solar=dict(r_rsun=cS.tolist(), abans=np.nan_to_num(gA2, nan=-1).tolist(), despres=np.nan_to_num(gD2, nan=-1).tolist(), capa=np.nan_to_num(gL2, nan=-1).tolist()))
    c1, g1, _ = ring_medians(Ld, d, Rm+16, 708, 1.0, SEL)
    g1s = ndi.gaussian_filter1d(np.interp(np.arange(len(g1)), np.nonzero(np.isfinite(g1))[0], g1[np.isfinite(g1)]), 2)
    pk1, pr1 = find_peaks(-g1s, prominence=0.001*np.nanmedian(g1s))
    res['V1_minims_locals_lunar'] = [dict(r_px=round(float(c1[p]), 1), prominencia_pct=round(float(100*pr1['prominences'][j]/g1s[p]), 3)) for j, p in enumerate(pk1)]
    # empremta no radial: la part de la màscara que no és rampa solar × porta lunar: mitjana per anell solar de (α/porta) on porta>0,5
    a = alpha_u16.astype(np.float32)/65535.
    ratio = np.where(gate_f32 > 0.5, a/np.maximum(gate_f32, 1e-3), np.nan)
    okr = SEL & np.isfinite(ratio) & ~PROT
    ca, pa, _ = ring_medians(np.nan_to_num(ratio), RS, 0.90, 12.0, 0.002, okr)
    fin = np.isfinite(pa)
    pa = np.interp(np.arange(len(pa)), np.nonzero(fin)[0], pa[fin]) if fin.any() else np.zeros(len(pa))   # anells sense prou píxels: interpolats, no zero
    idx = np.clip(np.digitize(RS, np.arange(0.90, 12.0+0.001, 0.002))-1, 0, len(pa)-1)
    a_rad = (pa[idx]*gate_f32).astype(np.float32); a_rad[~SEL] = 0
    Lr = lum(compose_over(abans_f, i, quantize(a_rad)))
    zona = SEL & (d >= Rm+3) & (RS <= 3.0) & ~PROT
    rel = (Ld[zona]-Lr[zona])/np.maximum(Lr[zona], 1e-4)
    res['empremta_no_radial_rms_pct'] = round(float(100*np.sqrt(np.mean(rel**2))), 4)
    res['empremta_no_radial_max_abs_pct'] = round(float(100*np.abs(rel).max()), 3)
    del Lr
    Qa = quantize(abans_f); Qd = quantize(despres_f)
    res['P3_nucli_px'] = int((np.asarray(P3) >= 1).sum()); res['P4_nucli_px'] = int((np.asarray(P4) >= 1).sum())
    core_rel = PCORE if i != 4 else (np.asarray(P3) >= 1)
    res['nuclis_dif_max_DN'] = int(np.abs(Qd[core_rel].astype(np.int32)-Qa[core_rel].astype(np.int32)).max()); res['nuclis_alpha_max'] = int(alpha_u16[core_rel].max())
    discs = {}
    for j in (3, 4, 5, 7, 8, 9, 10):
        dj, _, Rj = lunar_coords(j); zz = dj <= Rj+2
        discs[str(j)] = dict(px=int(zz.sum()), alpha_max=int(alpha_u16[zz].max()), dif_max_DN=int(np.abs(Qd[zz].astype(np.int32)-Qa[zz].astype(np.int32)).max()), propi=(j == i))
    res['discs_lunars'] = discs
    # disc propi (criteri) i unió dels discs de les capes INFERIORS (informatiu: la capa de dalt hi posa el seu propi limbe)
    dii, _, Rii = lunar_coords(i); own = dii <= Rii+2
    res['disc_propi'] = dict(px=int(own.sum()), alpha_max=int(alpha_u16[own].max()), dif_max_DN=int(np.abs(Qd[own].astype(np.int32)-Qa[own].astype(np.int32)).max()))
    fora = alpha_u16 == 0
    res['fora_suport_dif_max_DN'] = int(np.abs(Qd[fora].astype(np.int32)-Qa[fora].astype(np.int32)).max()); res['suport_px'] = int((~fora).sum())
    if extra: res.update(extra)
    ok = (res['n_minims_defecte'] == 0 and res['empremta_no_radial_rms_pct'] <= 0.5 and res['nuclis_dif_max_DN'] == 0 and res['fora_suport_dif_max_DN'] == 0
          and res['disc_propi']['dif_max_DN'] == 0 and res['disc_propi']['alpha_max'] == 0 and len(res['V1_minims_locals_lunar']) == 0)
    res['veredicte'] = 'ACCEPTADA' if ok else 'REBUTJADA'
    jdump(res, out_json); return res, Qa, Qd

_valid_cache = {}
def cell_validity(i, d, az, ring_edges, nsec, lunar=True):
    """Per cel·la: vàlida si p50≤0,46 i p95≤0,66 del canal màxim (píxels fora de P3/P4 i fora del disc propi) i r ≤ límit SNR≥5."""
    key = (i, lunar, len(ring_edges), nsec)
    if key in _valid_cache: return _valid_cache[key]
    mx, _ = layer_maxmin_canvas(i)
    di, _, Ri = lunar_coords(i)
    ok = frame_sel(i) & ~PROT & (di > Ri+3)
    rb = np.digitize(d, ring_edges)-1; sb = np.floor(az/(360./nsec)).astype(int) % nsec
    nr = len(ring_edges)-1
    V = np.zeros((nsec, nr), bool); P50 = np.full((nsec, nr), np.nan, np.float32); P95 = np.full((nsec, nr), np.nan, np.float32)
    inzone = ok & (rb >= 0) & (rb < nr)
    key_cell = (rb[inzone]*nsec + sb[inzone]); vals = mx[inzone]; rsv = RS[inzone]
    order = np.argsort(key_cell, kind='stable'); key_cell = key_cell[order]; vals = vals[order]; rsv = rsv[order]
    st = np.searchsorted(key_cell, np.arange(nr*nsec)); en = np.searchsorted(key_cell, np.arange(nr*nsec)+1)
    r_out = r_valid_outer(i, 5.0)
    for c in range(nr*nsec):
        if en[c]-st[c] < 20: continue
        v = vals[st[c]:en[c]]; p50, p95 = np.percentile(v, [50, 95]); r_med = float(np.median(rsv[st[c]:en[c]]))
        P50[c % nsec, c//nsec] = p50; P95[c % nsec, c//nsec] = p95
        V[c % nsec, c//nsec] = (p50 <= 0.46) and (p95 <= 0.66) and (r_med <= r_out)
    _valid_cache[key] = (V, P50, P95); del mx
    return V, P50, P95

def cell_mean(img, d, az, ring_edges, nsec, sel):
    rb = np.digitize(d, ring_edges)-1; sb = np.floor(az/(360./nsec)).astype(int) % nsec; nr = len(ring_edges)-1
    inz = sel & (rb >= 0) & (rb < nr)
    key = rb[inz]*nsec + sb[inz]
    s = np.bincount(key, weights=img[inz], minlength=nr*nsec); n = np.bincount(key, minlength=nr*nsec)
    M = np.full(nr*nsec, np.nan); M[n > 0] = s[n > 0]/n[n > 0]
    return M.reshape(nr, nsec).T, n.reshape(nr, nsec).T

def cobertura(masks, state_name, out_json, solar_rmax=3.0):
    """Contribució efectiva de les capes vàlides per cel·la; ≥0,9 fora de P3/P4 i de la banda declarada."""
    W = effective_weights(masks); ids = list(W)
    d7, az7, R7 = lunar_coords(7)
    rep = dict(state=state_name, zones={})
    for zname, (d, az, edges, nsec, lunar) in {
            'lunar_R+3_a_1.5Rsun': (d7, az7, np.arange(R7+3, 1.5*R_SUN+ (R7-R_SUN) + 1e-3, 4.0), 72, True),
            f'solar_1.5_a_{solar_rmax}Rsun': (RS, AZS, np.arange(1.5, solar_rmax+1e-3, 0.05), 24, False)}.items():
        cov = None; dom = None; dom_w = None
        for i in ids:
            V = cell_validity(i, d, az, edges, nsec, lunar)[0] if i != 3 else cell_validity(3, d, az, edges, nsec, lunar)[0]
            Wm, n = cell_mean(W[i], d, az, edges, nsec, SEL & ~PROT)
            Wm = np.nan_to_num(Wm)
            contrib = Wm*V
            cov = contrib if cov is None else cov + contrib
            if dom is None: dom = np.full(Wm.shape, i); dom_w = Wm.copy()
            else:
                better = Wm > dom_w; dom[better] = i; dom_w[better] = Wm[better]
        valid_cells = n >= 20
        bad = valid_cells & (cov < 0.9)
        rows = []
        for (s, r) in zip(*np.nonzero(bad)):
            rows.append(dict(sector_deg=float(s*360./nsec), r=float(edges[r]) if not lunar else float(edges[r]-R7), r_unit='px_sobre_R' if lunar else 'Rsun', cobertura=round(float(cov[s, r]), 3), dominant=int(dom[s, r])))
        rep['zones'][zname] = dict(n_cells=int(valid_cells.sum()), n_bad=int(bad.sum()), min_cobertura=round(float(np.nanmin(np.where(valid_cells, cov, np.nan))), 3),
                                   p01=round(float(np.nanpercentile(np.where(valid_cells, cov, np.nan), 1)), 3), bad_cells=rows[:60])
        print(f'  cobertura [{state_name}] {zname}: cel·les {valid_cells.sum()}, <0,9: {bad.sum()}, mínim {rep["zones"][zname]["min_cobertura"]}', flush=True)
    rep['ok'] = all(z['n_bad'] == 0 for z in rep['zones'].values())
    jdump(rep, out_json); return rep

def topmost_valid(d, az, edges, nsec, ids):
    T = np.zeros((nsec, len(edges)-1), int)
    for i in ids:
        V = cell_validity(i, d, az, edges, nsec, True)[0]; T[V] = i
    return T

def sectors_absolut(state_f, masks, state_name, out_json, nsec=72, dr=8.0, r1=120.0, thr=0.85):
    """Mediana lunar-cèntrica per cel·la (anell dr px × 5°) entre R+3 i R+r1. Un sector és SOT si queda < thr × la mediana
    dels 4 veïns de cada costat al mateix anell, la capa vàlida més alta hi és la mateixa que a tots els veïns (allà hauria de
    manar la mateixa capa) i el sot NO és a la pròpia capa (ratio compost < 0,9 × ratio de la capa sola: és màscara, no corona).
    Cel·les amb >30 % de P3/P4 s'exclouen (l'autoritat inferior hi mana per definició)."""
    L = lum(state_f); ids = [3] + sorted(masks)
    top = max(ids)
    d, az, Rm = lunar_coords(top)
    edges = np.arange(Rm+3, Rm+r1+1e-3, dr); nr = len(edges)-1
    _, S = sector_table(L, d, az, edges[0], edges[-1], dr, nsec, SEL)
    T = topmost_valid(d, az, edges, nsec, ids)
    layer_tables = {}
    for i in ids:
        _, layer_tables[i] = sector_table(lum(layer_rgb_canvas(i)), d, az, edges[0], edges[-1], dr, nsec, SEL)
    Pf, n = cell_mean(PROT.astype(np.float32), d, az, edges, nsec, SEL); Pf = np.nan_to_num(Pf)
    sots = []; worst = 1.0; n_tested = 0; n_raw = 0
    for r in range(nr):
        for s in range(nsec):
            v = S[s, r]
            if not np.isfinite(v) or Pf[s, r] > 0.30: continue
            ks = (-4, -3, -2, -1, 1, 2, 3, 4)
            nb = [S[(s+k) % nsec, r] for k in ks]; nb = [x for x in nb if np.isfinite(x)]
            if len(nb) < 6: continue
            same = all(T[(s+k) % nsec, r] == T[s, r] for k in ks) and T[s, r] > 0
            ratio = v/max(np.median(nb), 1e-6); n_tested += 1
            if not same: continue
            Lt = layer_tables[T[s, r]]; nbl = [Lt[(s+k) % nsec, r] for k in ks]; nbl = [x for x in nbl if np.isfinite(x)]
            ratio_layer = Lt[s, r]/max(np.median(nbl), 1e-6) if np.isfinite(Lt[s, r]) and nbl else np.nan
            if ratio < thr: n_raw += 1
            excess = ratio/ratio_layer if np.isfinite(ratio_layer) else ratio
            worst = min(worst, excess)
            if ratio < thr and excess < 0.9:
                sots.append(dict(sector_deg=s*360./nsec, r_px_sobre_R=round(float(edges[r]-Rm), 1), ratio=round(float(ratio), 3), ratio_capa=round(float(ratio_layer), 3), capa_valida=int(T[s, r]), mediana_DN=round(float(v*65535))))
    rep = dict(state=state_name, n_cells_tested=n_tested, n_sots=len(sots), n_cells_sota_085_abans_de_comparar_amb_capa=n_raw, pitjor_ratio_compost_sobre_capa=round(float(worst), 3), sots=sots[:80], ok=len(sots) == 0,
               taula_DN=(np.nan_to_num(S, nan=-1)*65535).round().astype(int).tolist(), r_edges_px_sobre_R=(edges-Rm).round(1).tolist())
    print(f'  sectors absolut [{state_name}]: {n_tested} cel·les, <0,85: {n_raw}, sots de màscara {len(sots)}, pitjor compost/capa {worst:.3f}', flush=True)
    jdump(rep, out_json); return rep

def r_a_cells(i, margin=0.01):
    """Primer radi solar on la capa és vàlida a TOTES les cel·les lunars (5° × 4 px): màxim del radi solar mitjà de les cel·les
    invàlides per saturació, + marge."""
    d7, az7, R7 = lunar_coords(7)
    edges = np.arange(R7+3, 1.5*R_SUN+(R7-R_SUN)+1e-3, 4.0)
    V, P50, P95 = cell_validity(i, d7, az7, edges, 72, True)
    Rc, n = cell_mean(RS, d7, az7, edges, 72, SEL)
    inv = (~V) & np.isfinite(P95) & ((P95 > 0.66) | (P50 > 0.46))
    return (round(float(np.nanmax(np.where(inv, Rc, np.nan)))+margin, 3) if inv.any() else None), int(inv.sum())

def pilots(states, names, out_prefix, lo_hi=None):
    """Fila per estat (retalls a,b,c de 1024 a 100 %) + fila de diferència (log2 després/abans, ±1,5 EV) entre consecutius."""
    from PIL import Image, ImageDraw
    d7, az7, R7 = lunar_coords(7); e7 = ell['7']
    ang = np.radians(150); pc = (e7['cx']+470*np.cos(ang), e7['cy']-470*np.sin(ang))
    pts = {'a_limbe_protuberancia': (3578, 2653), 'b_perles_diamant': (3607, 2585), 'c_banda_150deg': pc}
    out = {}
    for k, (cx, cy) in pts.items():
        x0 = int(np.clip(cx-512, 0, CW-1024)); y0 = int(np.clip(cy-512, 0, CH-1024))
        crops = [np.asarray(S[y0:y0+1024, x0:x0+1024], np.float32)/65535. for S in states]
        if lo_hi is None:
            lo, hi = np.percentile(lum(crops[-1]), [0.5, 99.5])
        else: lo, hi = lo_hi
        rows = [np.concatenate([stretch(c, lo, hi) for c in crops], 1)]
        difs = [np.full((1024, 1024, 3), 0.5, np.float32)]
        for a, b in zip(crops[:-1], crops[1:]):
            ev = np.log2(np.maximum(lum(b), 1e-4)/np.maximum(lum(a), 1e-4)); difs.append(np.repeat(np.clip(ev/3+0.5, 0, 1)[..., None], 3, 2))
        rows.append(np.concatenate(difs, 1))
        panel = np.concatenate(rows, 0)
        im = Image.fromarray((np.clip(panel, 0, 1)*255).astype(np.uint8)); dr = ImageDraw.Draw(im)
        for j, nm in enumerate(names):
            dr.text((j*1024+8, 8), nm, fill=(255, 80, 80)); dr.text((j*1024+8, 1024+8), f'log2({nm}/anterior) ±1,5 EV' if j else 'diferència', fill=(255, 80, 80))
        dr.text((8, 2048-20), f'{k} x={x0}..{x0+1024} y={y0}..{y0+1024} estirament {lo:.5f}-{hi:.5f} γ0,5', fill=(255, 80, 80))
        p = f'{out_prefix}_{k}.png'; im.save(p); out[k] = dict(path=p, x0=x0, y0=y0, lo=float(lo), hi=float(hi))
    return out

def overview(state_u16, path, scale=4):
    D = np.asarray(state_u16[::scale, ::scale], np.float32)/65535.; L = lum(D)
    lo, hi = np.percentile(L, [0.5, 99.8]); save_png(np.clip((D-lo)/(hi-lo), 0, 1)**0.35, path)

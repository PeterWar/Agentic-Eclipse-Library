"""a3 · Els 16 ràsters de filtre de la V86 (17 capes: la WOW bilateral va duplicada), fets des de la suma lineal verificada (a1).
Ús: python a3_filtres.py E1|E6|E2|E3|E4   (etapes independents; es poden córrer en paral·lel)
Entrades (rèplica exacta des dels RAW de la genealogia V58, 4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources):
  base_G.npy (G lineal de la fusió sense estrelles), fusion_starless.npy (RGB lineal), vixen/sony_starless.npy, support.npy.
Paràmetres de pantalla i de contrast: els mateixos rebuts que la V58 (vegeu PARAMS). Domini: suport físic fora del disc de presentació; a la franja, la dada d'un sol instant d'a3a.
Sortida: 4-RESULTATS/v86_neta_20260923/filtres/<tag>_u16.npy (+ _float.npy) i A3_<etapa>.json."""
from v88_comu import *
from v86_operadors import *
claim(); ETAPA = sys.argv[1]
C = SORT / 'filtres'; C.mkdir(parents=True, exist_ok=True)
ARX = ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay'
PARAMS = dict(display=ARX / 'filters_v58_dependencies/display', refined=ARX / 'v29_profiles_round1/cau/refined_detail_receipt.json',
              gran=ARX / 'v29_profiles_round1/cau/gran_azimuthal_receipt.json', variants=ARX / 'filters_v58_dependencies/fine_variants_receipt.json',
              sigma=V85D / 'fixed_inputs/resolution_sigma.npy', vixen_support=V85D / 'sources_v29/vixen_support.npy', sony_support=V85D / 'sources_v29/sony_support.npy',
              weight_vixen=V85D / 'b3_baseline/cau/weight_vixen_v42.npy', s4_npz=V85D / 's4_baseline/cau/s4_recomposicio_box.npz', s4_sup=V85D / 's4_baseline/cau/s4_support_new_box.npy')
def display(tag): d = json.loads((PARAMS['display'] / f'{tag}.json').read_text())['display']; return float(d['black']), float(d['white'])
# Franja amb dada d'un sol instant (a3a): la caixa de la Lluna porta les fonts lineals noves i el domini nou (fora del disc de presentació).
Q = np.load(SORT / 'A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = Q['box']; BOXQ = (slice(qy0, qy1), slice(qx0, qx1))
a = np.load(FONTS / 'base_G.npy'); m_sup = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
limits_hist = [float(a[m_sup].min()), float(a[m_sup].max())]          # terme global de l'MGN: els límits de la V84
a[BOXQ] = Q['G']; m = m_sup.copy(); m[BOXQ] = Q['domini'] & (a[BOXQ] > 0); franja = np.zeros((H, W), bool); franja[BOXQ] = Q['dins_franja']
r, t = coords(); rep = dict(etapa=ETAPA, franja='dada d un sol instant (a3a)', domini=dict(suport_original=int(m_sup.sum()), domini=int(m.sum())), entrades={k: str(v.relative_to(ARREL)) for k, v in PARAMS.items()})
def desa(tag, u, q=None, extra=None):
    np.save(C / f'{tag}_u16.npy', u)
    if q is not None: np.save(C / f'{tag}_float.npy', np.where(m, q, np.nan).astype('float32'))
    rep[tag] = dict(sha256_u16=sha(C / f'{tag}_u16.npy'), **(extra or {})); log(tag + ' FET')
def u_affine(q, lo, hi, dins=None):
    x = np.nan_to_num((q - lo) / (hi - lo), nan=0)
    if dins is not None: x = np.where(dins, x, 0)
    return np.round(np.clip(x, 0, 1) * 65535).astype('uint16')

if ETAPA == 'E1':       # NRGF, NRGF estès, RHEF i RHEF Υ: estadística per anell d'1 px sobre el domini (sense cap farcit)
    n, h, n2, xinfo, info = radial_v36(a, m, r, t); rep['radial'] = dict(info, **xinfo)
    for tag, q in [('P01_NRGF', n), ('P01_NRGF_extrap', n2)]:
        lo, hi = display(tag); assert np.isfinite(q[m]).all(); desa(tag, u_affine(q, lo, hi), q, dict(display=[lo, hi]))
    desa('P02_RHEF', u_affine(h, 0, 1), h, dict(display=[0, 1])); hu = upsilon(np.clip(h, 0, 1)); desa('P02b_RHEF_ups0.35', u_affine(hu, 0, 1), hu, dict(display=[0, 1], upsilon=.35))
elif ETAPA == 'E6':     # RHEF local nadiu 60° i 30°: CDF per sector a radi fix, mostres només del domini
    for deg, tag in [(60., 'P02c_RHEF_local60_native'), (30., 'P02d_RHEF_local30_native')]:
        q = rhef_native_cdf(a, m, r, t, deg, deg / 4); ok = m & np.isfinite(q)
        u = np.round(np.clip(np.nan_to_num(q, nan=.5), 0, 1) * 65535).astype('uint16'); np.save(C / f'{tag}_support.npy', ok)
        desa(tag, u, q, dict(sector_graus=deg, pas_graus=deg / 4, indefinits_al_domini=int((m & ~np.isfinite(q)).sum())))
elif ETAPA == 'E2':     # MGN, WOW, WOW bilateral: operadors espacials amb la condició de contorn nova fora del domini
    L = np.where(m, np.log(np.maximum(a, 1e-9)), 0).astype('float32'); Lf, finfo = continua_ln(L, m, r); ent = np.where(m, a, np.exp(Lf)).astype('float32'); del L, Lf; gc.collect()
    rep['contorn'] = finfo; full = np.ones((H, W), bool); limits = limits_hist
    for tag in ['P04_WOW', 'P05_WOW_bilateral', 'P03_MGN']:
        log(tag + ' comença')
        if tag == 'P03_MGN': q = mgn(np.maximum(ent, 0), full, limits=limits)
        else: q = wow(ent, full, 11, tag == 'P05_WOW_bilateral')
        lo, hi = display(tag); assert np.isfinite(q[m]).all(); desa(tag, u_affine(q, lo, hi), q, dict(display=[lo, hi], **({'limits_globals': limits} if tag == 'P03_MGN' else {'escales': 11})))
        del q; gc.collect()
elif ETAPA == 'E3':     # ACHF isòtrop 01/04/05/06 per canal sobre ln I, mediana dels tres canals, tanh, S/N, anivellament i suavitzat exterior
    total = np.array(np.load(FONTS / 'fusion_starless.npy', mmap_mode='r')); total[BOXQ] = Q['F']; old = json.loads(PARAMS['refined'].read_text()); profiles = old['profiles']; var = json.loads(PARAMS['variants'].read_text())['variants']
    sigmamap = np.load(PARAMS['sigma'], mmap_mode='r')
    layers = {'01': ((2, 4, 8, 16, 32), 'refined:achf', 3.), '04': ((1, 2, 4, 8, 16), 'variants:micro1_16', 1.5), '05': ((2, 4, 8, 16, 32, 48), 'variants:fi2_48', 3.), '06': ((4, 8, 16, 32, 64), 'variants:estructura4_64', 3.)}
    all_sigmas = sorted(set(s for v in layers.values() for s in v[0])); tmp = {}
    for ch in range(3):
        good = m & (np.asarray(total[..., ch]) > 0); x = np.log(np.maximum(np.asarray(total[..., ch]), 1e-8)).astype('float32'); x, frep = continua_ln(x, good, r); rep[f'contorn_canal{ch}'] = frep
        w = np.ones((H, W), np.float32); p = profiles[str(ch)]; scale = np.interp(np.log(np.maximum(r / RS, 1e-5)), p['lnr_centres'], p['robust_contrast']).astype('float32'); acc = {k: np.zeros((H, W), np.float32) for k in layers}
        for sig in all_sigmas:
            band = x - normgauss(x, w, sig)
            for k, v in layers.items():
                if sig in v[0]: acc[k] += band / len(v[0])
            log(f'  canal {ch} sigma {sig}')
        for k in layers: tmp[k, ch] = C / f'iso_{k}_{ch}_tmp.npy'; np.save(tmp[k, ch], np.where(good, acc[k] / scale, np.nan).astype('float32'))
        del acc, x, good, w, band, scale; gc.collect()
    wsup = m.astype('float32'); ctx = h1_setup(r, m)
    for k, (sigmas, ts, se) in layers.items():
        reals = [np.load(tmp[k, ch], mmap_mode='r') for ch in range(3)]; d = np.zeros((H, W), np.float32)
        for y0 in range(0, H, 256): d[y0:y0 + 256] = np.nan_to_num(np.nanmedian(np.stack([q[y0:y0 + 256] for q in reals]), axis=0), nan=0)
        kind, key = ts.split(':'); sc = old['filters'][key]['scale_tanh'] if kind == 'refined' else var[key]['scale_tanh']
        mapped = (.5 * np.tanh(d / max(sc, 1e-6))).astype('float32'); sm = sn_smooth(mapped, m, sigmamap); centered, hist = centre_rings(sm, m, r)
        aa = np.clip(.5 + centered, 0, 1); aa[~m] = .5; den = gauss(wsup, se); b = .5 + gauss((aa - .5) * wsup, se) / np.maximum(den, 1e-8); b[~m] = .5
        desa(k, np.round(np.clip(b, 0, 1) * 65535).astype('uint16'), d, dict(sigmas=sigmas, scale_tanh=sc, external_sigma=se, H1=h1(b, m, ctx)['worst'], H1_history=hist))
        for ch in range(3): tmp[k, ch].unlink()
        del reals, d, mapped, sm, centered, aa, b; gc.collect()
elif ETAPA == 'E4':     # ACHF angular 03 / 03v30 / 07: pas alt al llarg de l'arc a cada tren, suavitzat radial 0/4/8 px, pes Vixen/Sony de la V42
    old = json.loads(PARAMS['gran'].read_text()); profiles = old['post_contrast_profiles']; mv = np.load(PARAMS['vixen_support']); ms = np.load(PARAMS['sony_support'])
    z = np.load(PARAMS['s4_npz']); y0, y1, x0, x1 = z['box'].astype(int); mv[y0:y1, x0:x1] |= np.load(PARAMS['s4_sup'])
    V = np.array(np.load(FONTS / 'vixen_starless.npy', mmap_mode='r')[..., 1]); V[BOXQ] = Q['V']; SS = np.load(FONTS / 'sony_starless.npy', mmap_mode='r')[..., 1]
    mv[BOXQ] = Q['domini']; ms[BOXQ] &= Q['domini'] & ~Q['dins_franja']      # franja: només la Vixen d'un instant; la Sony no hi entra
    masks = {'vixen': mv & np.isfinite(V) & (V > 0), 'sony': ms & np.isfinite(SS) & (SS > 0)}; mm = masks['vixen'] | masks['sony']
    wv = np.load(PARAMS['weight_vixen']); wv = np.where(masks['sony'], wv, masks['vixen'].astype('float32')) * masks['vixen']; ws = (1 - wv) * masks['sony']
    sigmamap = np.load(PARAMS['sigma'], mmap_mode='r'); bands = {}; keys = {'03': 0., '03v30': 4., '07': 8.}
    for tag, src, mask in [('vixen', V, masks['vixen']), ('sony', SS, masks['sony'])]:
        log('polar ' + tag); p, valid, r0, nt = angular_polar(np.log(np.maximum(np.asarray(src), 1e-8)), mask, r, t)
        for key, sr in keys.items():
            q = p if sr == 0 else gaussian_filter1d(p * valid, sr, axis=0, mode='constant', cval=0) / np.maximum(gaussian_filter1d(valid, sr, axis=0, mode='constant', cval=0), 1e-8)
            bands[tag, key] = back(q, mask, r, t, r0, nt).astype('float32'); log(tag + ' ' + key)
        del p, valid, q; gc.collect()
    scale = np.zeros((H, W), np.float32)
    for tag, w in [('vixen', wv), ('sony', ws)]:
        pr = profiles[tag]; scale += w * np.interp(np.log(np.maximum(r / RS, 1e-5)), pr['lnr_centres'], pr['robust_contrast']).astype('float32')
    ctx = h1_setup(r, mm)
    for key, sr in keys.items():
        d = wv * bands['vixen', key] + ws * bands['sony', key]; d = np.where(mm, d / np.maximum(scale, .002), 0).astype('float32')
        mapped = (.5 * np.tanh(d / old['scale_tanh'])).astype('float32'); sm = sn_smooth(mapped, mm, sigmamap); centered, hist = centre_rings(sm, mm, r)
        aa = np.clip(.5 + centered, 0, 1); aa[~mm] = .5; u = np.round(aa * 65535).astype('uint16'); u[~mm] = 32768
        desa(key, u, d, dict(sigma_radial=sr, H1=h1(aa, mm, ctx)['worst'], H1_history=hist))
    np.save(C / 'angular_support.npy', mm)
desa_json(f'A3_{ETAPA}.json', rep); log('ETAPA ' + ETAPA + ' COMPLETA')

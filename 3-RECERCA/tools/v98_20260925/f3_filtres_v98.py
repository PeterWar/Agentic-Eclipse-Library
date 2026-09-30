"""f3 (V98) · Els 16 filtres de la V97 (f3_filtres_v97.py) amb NOMÉS aquests canvis (V97_Artefactes de Pere i pla de Codex del 25-09):
  · la franja: A3B (a3b_franja_neta.py: selecció física per fotograma, cap suavitzat) en lloc de l'A3A (11 fotogrames suavitzats σ 1,3);
    variable V98_FRANJA (npz amb el mateix format);
  · la Lluna neta: alfa 0 a TOT el disc de presentació (d < 0), també a les capes en Multiplicar (a la V97 hi tenien alfa 1 i el nivell de l'arc,
    els «radis»); el nivell de la decisió B només al buit de FORA del disc (0 ≤ d < vora de la dada), amb rampa d'1 px a d = 0;
  · WOW: sense la «vora difuminada» (només parells a la mateixa distància del limbe a d < 12 px de la cresta): era per al dèficit de vora de la
    franja d'un instant, que la dada A3B ja no té (opció --wow-vora cresta per comparar);
  · MGN i ACHF isòtrops: la mitjana local és una CONVOLUCIÓ NORMALITZADA D'ORDRE 1 (pla local, Knutsson i Westin 1993): a la vora de la dada,
    la mitjana d'ordre 0 d'un sol costat té el biaix del gradient radial (banda clara a l'MGN, banda a tot el limbe a l'ACHF micro, marca 304
    de Pere). On el suport és complet i simètric, l'ordre 1 dona EXACTAMENT la mitjana d'ordre 0 (mateix nucli), o sigui, lluny de les vores
    el filtre és el de la V97 (opció --ordre 0 per comparar).
Tota la resta, idèntica a la V97:
f3 (V97) · Els 16 ràsters de filtre des de la linealitzada V97, amb les regles de la V97 (vegeu PLA_V97.md):
  · entrada NOMÉS de dada: el domini = suport fora del disc de presentació + la franja amb dada d'un sol instant (A3A); cap continuació
    (ni a4v, ni a5d, ni continua_ln, ni pull-push): els operadors espacials fan convolució normalitzada pel domini;
  · al buit (el disc i els 1–2 px sense dada arran del limbe): en Multiplicar (41–46) NOMÉS el nivell del filtre als primers píxels de dada
    al llarg de l'arc (decisió B de Pere, 24-09); en Superposar/Diferència (47–56) transparent (alfa 0, fosa d'1,5 px a la vora de la dada);
  · anells parcials interiors completats amb el patró azimutal dels 40 anells complets de sobre (NRGF, com la V96; RHEF, amb la CDF de z
    dels anells complets): cura el cercle a r_in;
  · els ACHF isòtrops (01/04/05/06) sobre la LLUMINÀNCIA ln((R+2G+B)/4), no canal per canal: el color no entra al detall (research/105);
  · les WOW, l'operador V95 amb la rampa de completesa de les escales gruixudes més ampla (A5: arcs lila d'entrada de les escales 5 i 6).
Mateixos paràmetres de pantalla que la V58/V96 (rebuts de raw_replay), perquè lluny del limbe l'aspecte sigui el mateix.
Ús (etapes independents, en paral·lel): V97_SORT=<sortida> V97_FONTS=<linealitzada d4> f3_filtres_v97.py E1|E6|E2|E3|E4 [--wow-llindar 0.6]
La franja A3A es llegeix de $V97_SORT/A3A_franja_un_instant.npz. Sortida: $V97_SORT/filtres/<tag>_u16.npy, <tag>_alfa_u16.npy, F3_<etapa>.json."""
import sys, os, argparse, gc
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v97_refundacio_20260924'))
from v97_comu import *
from v86_operadors import (gauss, normgauss, ng, sn_smooth, centre_rings, h1_setup, h1, ring_stats, complete_from_partial, rhef_native_cdf, mgn,
                           angular_polar, back, upsilon, smoothstep, NB)
from scipy.ndimage import gaussian_filter1d
import cv2
ap = argparse.ArgumentParser(); ap.add_argument('etapa'); ap.add_argument('--wow-llindar', type=float, default=0.6); ap.add_argument('--caixa', help='x0,y0,x1,y1 (només proves)'); ap.add_argument('--wow-vora', choices=['cap', 'cresta'], default='cap'); ap.add_argument('--ordre', type=int, choices=[0, 1], default=1); ap.add_argument('--rhef-sim', choices=['si', 'no'], default='si'); ap.add_argument('--rhef-pas', type=float, default=4.0); ap.add_argument('--rhef-fosa', type=float, default=60.0); ap.add_argument('--rhef-detrend', choices=['si', 'no'], default='no'); ap.add_argument('--retalla-vora', type=float, default=0.0, help='NOMÉS PROVES (d13/d14): treu del domini els primers N px de dada arran del limbe')
A = ap.parse_args(); ETAPA = A.etapa; claim()
C = SORT / 'filtres'; C.mkdir(parents=True, exist_ok=True)
ARX = ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay'
PARAMS = dict(display=ARX / 'filters_v58_dependencies/display', refined=ARX / 'v29_profiles_round1/cau/refined_detail_receipt.json',
              gran=ARX / 'v29_profiles_round1/cau/gran_azimuthal_receipt.json', variants=ARX / 'filters_v58_dependencies/fine_variants_receipt.json',
              sigma=ARREL / '4-RESULTATS/v85_regeneracio_20260922/fixed_inputs/resolution_sigma.npy',
              vixen_support=V85D / 'sources_v29/vixen_support.npy', sony_support=V85D / 'sources_v29/sony_support.npy',
              weight_vixen=Path(os.environ.get('V97_WV', RES / 'cadena_v97/b3/cau/weight_vixen_v42.npy')),
              s4_npz=V85D / 's4_baseline/cau/s4_recomposicio_box.npz', s4_sup=V85D / 's4_baseline/cau/s4_support_new_box.npy')
def display(tag): d = json.loads((PARAMS['display'] / f'{tag}.json').read_text())['display']; return float(d['black']), float(d['white'])
LIMITS_MGN = [float(v) for v in json.loads((ARREL / '4-RESULTATS/v88_20260923/A3_E2.json').read_text()).get('P03_MGN', {}).get('limits_globals', [])] or None
# ---------- fonts i domini ----------
Q = np.load(os.environ['V98_FRANJA']); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; BOXQ = (slice(qy0, qy1), slice(qx0, qx1))
cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NBZ = len(DMIN)
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m_sup = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
a[BOXQ] = Q['G']; m = m_sup.copy(); m[BOXQ] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
if A.retalla_vora > 0:   # NOMÉS PROVES: el vorell es desplaça amb la vora (operador) o es queda (dada)?
    _yy, _xx = np.mgrid[qy0:qy1, qx0:qx1]; _d = np.hypot(_xx - cx, _yy - cy) - R; _th = (np.degrees(np.arctan2(-(_yy - cy), _xx - cx)) + 360) % 360
    _dv = _d - np.maximum(DMIN, 0)[(_th / 360 * NBZ).astype(int) % NBZ]; m[BOXQ] &= ~((_dv < A.retalla_vora) & (_d < 45))
DOMQ = Q['domini'] & m[BOXQ] if A.retalla_vora > 0 else Q['domini']
r, t = coords(); rep = dict(etapa=ETAPA, fonts=str(FONTS), franja=os.environ['V98_FRANJA'], wow_vora=A.wow_vora, ordre_mitjana_local=A.ordre, domini=int(m.sum()), capes={})
yy, xx = np.ogrid[:H, :W]; dL = (np.hypot(xx - cx, yy - cy) - R).astype(np.float32)          # distància al limbe de presentació
thL = ((np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360).astype(np.float32)
def alfa_domini(mm, fosa=1.5):
    """0 sense dada, 1 amb dada, fosa d'1,5 px a la vora de la dada (a la Lluna, sobre la corba contínua d − DMIN(θ)), com la V94/V95."""
    dist = cv2.distanceTransform(mm.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32); al = smoothstep(dist, 0.0, 1.5) * mm
    d = dL[BOXQ]; dv = d - np.maximum(DMIN, 0)[(thL[BOXQ] / 360 * NBZ).astype(int) % NBZ]; aprop = smoothstep(dv, 0.0, fosa) * mm[BOXQ]   # V98: la vora real és max(DMIN, 0)
    al[BOXQ] = np.where(d < 40, aprop, al[BOXQ]); al = al * np.clip(dL, 0, 1)      # V98: cap píxel dins del disc de presentació
    return np.round(al * 65535).astype(np.uint16)
def nivell_buit(u01, mm, fosa=(0.0, 1.5)):
    """Decisió B de Pere (24-09) per a les capes en Multiplicar: al buit, NOMÉS el nivell del filtre als primers píxels de dada (1 ≤ d − DMIN < 3)
    al llarg de l'arc (gaussiana σ 3 px d'arc), sense textura; també dins del disc (tapat per la Lluna opaca). Fora de la caixa, sense dada → 0,5."""
    out = u01.copy(); d = dL[BOXQ]; th = thL[BOXQ]; dist = d - np.maximum(DMIN, 0)[(th / 360 * NBZ).astype(int) % NBZ]; mb = mm[BOXQ]; ub = out[BOXQ]   # V98: vora de la dada, mai dins del disc
    NT = 3600; tb = (th / 360 * NT).astype(int) % NT; zona = mb & (dist >= 2) & (dist < 8)   # V98: 2–8 px (a 1–3 px el rang de la RHEF local hi és extrem)
    s = np.bincount(tb[zona], weights=ub[zona], minlength=NT); n = np.bincount(tb[zona], minlength=NT).astype(float); sig = 3.0 / (R * np.radians(360 / NT))
    L = (gaussian_filter1d(s, sig, mode='wrap') / np.maximum(gaussian_filter1d(n, sig, mode='wrap'), 1e-9))[tb].astype(np.float32)
    buit = (~mb) & (d >= 0) & (d < 45); ub = np.where(buit, L, ub)     # V98: només el buit de FORA del disc
    zf = mb & (dist >= 0) & (dist < fosa[1]) & (d < 45)                # V98: la primera filera de dada passa al nivell (1,5 px, la mateixa fosa que l'alfa
    wfs = smoothstep(dist, fosa[0], fosa[1]); ub = np.where(zf, L + (ub - L) * wfs, ub)   # de les capes en Superposar); a les RHEF locals, 1 → 3 px (d13)
    out[BOXQ] = ub; out[~mm & ~np.pad(np.ones_like(mb), ((qy0, H - qy1), (qx0, W - qx1)))] = 0.5
    return out, int(buit.sum())
def desa(tag, u01=None, u16=None, alfa=None, extra=None, mult=False):
    if u16 is None: u16 = np.round(np.clip(np.nan_to_num(u01, nan=0.5), 0, 1) * 65535).astype(np.uint16)
    np.save(C / f'{tag}_u16.npy', u16)
    al = np.round(np.clip(dL, 0, 1) * 65535).astype(np.uint16) if mult else (alfa if alfa is not None else alfa_domini(m))   # V98: Multiplicar també amb alfa 0 dins del disc
    np.save(C / f'{tag}_alfa_u16.npy', al)
    rep['capes'][tag] = dict(sha256_u16=sha(C / f'{tag}_u16.npy'), mode='Multiplicar (nivell al buit de fora del disc; alfa 0 dins)' if mult else 'transparent sense dada i dins del disc', **(extra or {})); log(tag + ' FET')
def u_affine(q, lo, hi): return np.clip((q - lo) / (hi - lo), 0, 1).astype(np.float32)
import numexpr as ne
sys.path.insert(0, str(Path(__file__).resolve().parent)); from rhef_local_sim import rhef_local_sim
from angular_polar1 import angular_polar1
def conv_ordre1(a, w, s, ksize, border):
    """Convolució normalitzada d'ORDRE 1 (Knutsson i Westin 1993): a cada píxel, el valor en x del pla local a + b·u ajustat per mínims quadrats
    ponderats (nucli gaussià g(u) × pes de dada w(x+u)). Amb suport complet i simètric els termes lineals s'anul·len i el resultat és exactament
    la mitjana d'ordre 0 amb el mateix nucli; a la vora de la dada treu el biaix del gradient. On el sistema és degenerat (suport en una línia),
    l'ordre 0. Retorna (mitjana, q) amb q = det/(m00·m20·m02) ∈ (0, 1] (1 = suport simètric)."""
    k = cv2.getGaussianKernel(ksize, s).astype(np.float64).ravel(); u = (np.arange(ksize) - ksize // 2) / s
    k0 = k.astype(np.float32); k1 = (k * u).astype(np.float32); k2 = (k * u * u).astype(np.float32)
    f = lambda img, kx, ky: cv2.sepFilter2D(img, cv2.CV_32F, kx, ky, borderType=border)
    wf = np.asarray(w, np.float32); aw = (np.asarray(a, np.float32) * wf).astype(np.float32)
    m00 = f(wf, k0, k0); m10 = f(wf, k1, k0); m01 = f(wf, k0, k1); m20 = f(wf, k2, k0); m02 = f(wf, k0, k2); m11 = f(wf, k1, k1)
    b0 = f(aw, k0, k0); b1 = f(aw, k1, k0); b2 = f(aw, k0, k1); del aw
    C00 = ne.evaluate('m20*m02 - m11*m11'); C01 = ne.evaluate('-(m10*m02 - m01*m11)'); C02 = ne.evaluate('m10*m11 - m20*m01')
    det = ne.evaluate('m00*C00 + m10*C01 + m01*C02'); q = ne.evaluate('det / where(m00*m20*m02 > 1e-30, m00*m20*m02, 1e-30)')
    o1 = ne.evaluate('(C00*b0 + C01*b1 + C02*b2) / where(abs(det) > 1e-30, det, 1e-30)'); o0 = ne.evaluate('b0 / where(m00 > 1e-20, m00, 1e-20)')
    out = np.where(q > 0.02, o1, o0).astype(np.float32); return out, q.astype(np.float32)
def normgauss1(a, w, s):
    """Com v86_operadors.normgauss (cv2.GaussianBlur, nucli fins a 4σ, BORDER_REFLECT_101), d'ordre 1."""
    ks = int(round(s * 4 * 2 + 1)) | 1; return conv_ordre1(np.where(w > 0, a, 0), (w > 0).astype(np.float32) * w, s, ks, cv2.BORDER_REFLECT_101)[0]
def ng1(a, m, s, truncate=3):
    """Com v86_operadors.ng (nucli fins a 3σ, BORDER_REPLICATE), d'ordre 1."""
    return conv_ordre1(np.where(m, a, 0), m.astype(np.float32), s, 2 * int(truncate * s + .5) + 1, cv2.BORDER_REPLICATE)[0]
def mgn1(a, m, sigmas=(1.25, 2.5, 5, 10, 20, 40), k=.7, h=.7, gamma=3.2, limits=None):
    """v86_operadors.mgn amb la mitjana local d'ordre 1 (la variància local, com l'original)."""
    from v86_operadors import ng as _ng
    lo, hi = limits or (float(np.min(a[m])), float(np.max(a[m]))); detail = np.zeros_like(a, dtype='float32')
    for s_ in sigmas:
        mu = ng1(a, m, s_); d = a - mu
        d[np.abs(d) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(a), np.abs(mu))] = 0
        den = np.sqrt(_ng(d * d, m, s_)); z = np.divide(d, den, out=np.zeros_like(d), where=den > 0)
        detail += np.arctan(k * z) / len(sigmas); log('  MGN (ordre 1) sigma ' + str(s_))
    global_term = np.clip((a - lo) / (hi - lo), 0, 1) ** (1 / gamma)
    return h * global_term + (1 - h) * detail

if ETAPA == 'E1':   # NRGF (41), NRGF estès (42), RHEF (43), RHEF Υ (44) · anells d'1 px centrats al Sol, només dada; anells interiors completats
    ri = np.floor(r).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; v = a[m].astype('float64'); tb = np.floor((t[m] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB
    count, mean, std = ring_stats(v, ids, nr); good = count > 0; nodes = np.arange(nr) + .5
    comp = count / (2 * np.pi * nodes); refc = np.median(comp[int(3 * RS):int(8 * RS)])
    cand_out = np.flatnonzero((nodes > 3 * RS) & (comp < 0.98 * refc)); r_edge = int(cand_out[0]) if cand_out.size else nr
    r_in = int(np.flatnonzero((comp >= 0.98 * refc) & (nodes > 0.9 * RS))[0])
    inner = [i for i in range(r_in) if count[i] > 0]; outer = list(range(r_edge, nr)); log(f'r_in {r_in} · r_edge {r_edge} · anells interiors {len(inner)}')
    mean_u, std_u, ok_o, _, _ = complete_from_partial(mean, std, ids, tb, v, outer, list(range(r_edge - 40, r_edge)))
    mean_u, std_u2, ok_i, _, _ = complete_from_partial(mean_u, std_u, ids, tb, v, inner, list(range(r_in, r_in + 40)))
    ok_ring = good & ok_o & ok_i
    mu = np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32'); sd = np.interp(r, nodes[ok_ring], std_u2[ok_ring]).astype('float32')
    z = np.divide(a - mu, sd, out=np.zeros_like(a), where=sd > 0).astype('float32'); del mu, sd
    # 42: NRGF estès cap endins (μ, σ log-lineals ajustades a r_in…r_in+40), la recepta de la V58/V96
    kk = np.arange(r_in, r_in + 40); okk = ok_ring[kk] & (mean_u[kk] > 0) & (std_u2[kk] > 0)
    pm = np.polyfit(nodes[kk][okk], np.log(mean_u[kk][okk]), 1); ps = np.polyfit(nodes[kk][okk], np.log(std_u2[kk][okk]), 1)
    mean_x = mean_u.copy(); std_x = std_u2.copy(); ok_x = ok_ring.copy()
    for i in range(r_in):
        if count[i] > 0: mean_x[i] = np.exp(np.polyval(pm, nodes[i])); std_x[i] = np.exp(np.polyval(ps, nodes[i])); ok_x[i] = True
    mu2 = np.interp(r, nodes[ok_x], mean_x[ok_x]).astype('float32'); sd2 = np.interp(r, nodes[ok_x], std_x[ok_x]).astype('float32')
    z2 = np.divide(a - mu2, sd2, out=np.zeros_like(a), where=sd2 > 0).astype('float32'); del mu2, sd2
    # V97: la 42 (NRGF estès cap endins) també amb els anells interiors COMPLETATS (la μ, σ log-lineals de la V58 feien el cercle a r_in per
    # construcció: el jutge A4 ho va mesurar, −0,0034 de salt medià). Queda la 41 amb el rang de pantalla de la 42; retirar-la és decisió de Pere.
    for tag, q in (('P01_NRGF', z), ('P01_NRGF_extrap', z)):
        lo, hi = display(tag); u = np.where(m, u_affine(q, lo, hi), 0.5); u, nb = nivell_buit(u, m)
        desa(tag, u, mult=True, extra=dict(display=[lo, hi], r_in=r_in, r_edge=r_edge, anells_interiors_completats=len(inner), px_buit_nivell=nb))
    # RHEF (43, 44): CDF empírica per anell (la de la V58) i, als anells PARCIALS interiors (r < r_in) i a la vora del llenç, la CDF de z
    # (amb μ, σ completades) dels 40 anells complets veïns, amb fosa de 8 px: el rang de l'arc visible d'un anell parcial és esbiaixat.
    flat = np.flatnonzero(m); rflat = r.ravel()[flat]; order = np.argsort(ri.ravel()[flat], kind='stable'); flat_o = flat[order]
    counts = np.bincount(ri.ravel()[flat_o], minlength=nr); cuts = np.r_[0, np.cumsum(counts)]; af = a.ravel()
    sorted_rings = [np.sort(af[flat_o[cuts[i]:cuts[i + 1]]]) for i in range(nr)]
    def Fr(i, vals):
        s = sorted_rings[i]
        if len(s) == 0: return np.full(vals.shape, np.nan, 'float32')
        return (np.searchsorted(s, vals, side='left') + np.searchsorted(s, vals, side='right')).astype('float32') / (2.0 * len(s))
    rh = np.zeros(len(flat), 'float32'); vals = af[flat]; i0 = np.clip(np.floor(rflat - 0.5).astype('int32'), 0, nr - 1); i1 = np.clip(i0 + 1, 0, nr - 1); al_ = np.clip(rflat - (i0 + 0.5), 0, 1).astype('float32')
    for i in range(nr):
        k = np.flatnonzero(i0 == i)
        if not k.size: continue
        f0 = Fr(i, vals[k]); f1 = Fr(min(i + 1, nr - 1), vals[k]); f1 = np.where(np.isfinite(f1), f1, f0); f0 = np.where(np.isfinite(f0), f0, f1); rh[k] = (1 - al_[k]) * f0 + al_[k] * f1
    rhef = np.zeros_like(a).ravel(); rhef[flat] = rh; rhef = rhef.reshape(a.shape); zf = z.ravel()[flat]
    def Fz(rings):
        ks = np.isin(ids, rings); zz = (v[ks] - mean_u[ids[ks]]) / np.maximum(std_u2[ids[ks]], 1e-12); zs = np.sort(zz); return lambda q: np.searchsorted(zs, q, side='right') / len(zs)
    Fin = Fz(list(range(r_in, r_in + 40))); Fout = Fz(list(range(r_edge - 40, r_edge)))
    w_in = 1 - smoothstep(rflat, r_in - 4, r_in + A.rhef_fosa); w_out = smoothstep(rflat, r_edge - 64 - 32, r_edge - 32)   # V98: fosa de 8 → 64 px (la de 8 px feia l'arc de r_in a ~14 px sobre la Lluna, marques P02/P02b de Pere)
    rhf = rhef.ravel()[flat]; rhf = (1 - w_in) * rhf + w_in * Fin(zf).astype('float32'); rhf = (1 - w_out) * rhf + w_out * Fout(zf).astype('float32')
    rhef = np.full(a.shape, 0.5, np.float32); rhef.ravel()[flat] = rhf
    u, nb = nivell_buit(np.where(m, rhef, 0.5), m); desa('P02_RHEF', u, mult=True, extra=dict(display=[0, 1], px_buit_nivell=nb, anells_interiors=f'CDF de z dels 40 anells complets (fosa r_in − 4 … r_in + {A.rhef_fosa:.0f} px)'))
    hu = upsilon(np.where(m, np.clip(rhef, 0, 1), np.nan)); u, nb = nivell_buit(np.where(m, hu, 0.5), m); desa('P02b_RHEF_ups0.35', u, mult=True, extra=dict(upsilon=.35, px_buit_nivell=nb))
elif ETAPA == 'E6':  # RHEF local 60° i 30° (45, 46): CDF per sector a radi fix, mostres només del domini; cel·les indefinides → nivell (com el buit)
    for deg, tag in ((60., 'P02c_RHEF_local60_native'), (30., 'P02d_RHEF_local30_native')):
        q = rhef_local_sim(a, m, r, t, deg, deg / A.rhef_pas, CX, CY, log=log, simetric=A.rhef_sim == 'si', detrend=A.rhef_detrend == 'si', nmin=200); ok = m & np.isfinite(q)   # V98: parells simètrics (rhef_local_sim.py)
        u, nb = nivell_buit(np.where(ok, q, 0.5).astype(np.float32), ok, fosa=(1.0, 3.0))   # V98 (d13): el rang local dels 2 primers px és un efecte de vora de l'operador
        indef = m & ~np.isfinite(q)
        desa(tag, u, mult=True, extra=dict(sector_graus=deg, pas_graus=deg / A.rhef_pas, parells_simetrics=A.rhef_sim, rang_contra_tendencia_a_la_vora=A.rhef_detrend, indefinits_al_domini=int(indef.sum()), indefinits_lluny_limbe=int((indef & (dL > 45)).sum()), px_buit_nivell=nb))
elif ETAPA == 'E2':  # WOW (55), WOW bilateral (56) amb l'operador V95; MGN (54) només sobre el domini
    sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v95_20260924')); from wow_v95 import wow_v95, desplacament_cresta, dmap_vora
    if A.wow_vora == 'cresta':
        dmap = dL.copy(); off, cresta = desplacament_cresta(Q['G'], Q['domini'] & (Q['G'] > 0), (qy0, qx0), cx, cy, R); dmap = dmap_vora(dmap, xx, yy, cx, cy, off)
    else: dmap = np.full((H, W), 1e4, np.float32)      # V98: cap zona especial de vora (la dada A3B no té el dèficit que la justificava)
    SIG = lambda s: min(150.0, max(32.0, 4.0 * 2 ** s)); L0 = A.wow_llindar
    PARAM = {'P05_WOW_bilateral': dict(centra_rad=True, iso=(0.5, 1.5), sig_rad=SIG, llindar=lambda s: (L0, 0.995)), 'P04_WOW': dict(centra_rad=True, iso=(0.25, 0.75), sig_rad=SIG, llindar=lambda s: (L0, 0.995))}
    K_V95 = {'P05_WOW_bilateral': 0.02317, 'P04_WOW': 0.03709}   # escala de pantalla de la V95 (W1_WOW.json), fixa
    for tag, bil in (('P05_WOW_bilateral', True), ('P04_WOW', False)):
        q, _, mus = wow_v95(a, m, dmap, 8, bil, log=log, **PARAM[tag]); disp = np.where(m, 0.5 + K_V95[tag] * np.nan_to_num(q), 0.5)
        desa(tag, disp, extra=dict(k=K_V95[tag], llindar_completesa=[L0, 0.995], mitjanes_escala=[round(float(x), 5) for x in mus])); del q, disp; gc.collect()
    q = (mgn1 if A.ordre == 1 else mgn)(np.maximum(a, 0), m, limits=LIMITS_MGN); lo, hi = display('P03_MGN'); desa('P03_MGN', np.where(m, u_affine(q, lo, hi), 0.5), extra=dict(display=[lo, hi], limits=LIMITS_MGN, entrada='només el domini (convolució normalitzada), sense continua_ln'))
elif ETAPA == 'E3':  # ACHF isòtrop 01/04/05/06 (50, 51, 52, 53) sobre ln de la LLUMINÀNCIA, convolució normalitzada pel domini
    F = np.array(np.load(FONTS / 'fusion_starless.npy', mmap_mode='r')); F[BOXQ] = Q['F']
    Lm = (F[..., 0] + 2 * F[..., 1] + F[..., 2]) / 4; del F; gc.collect(); good = m & (Lm > 0)
    x = np.where(good, np.log(np.maximum(Lm, 1e-8)), 0).astype('float32'); del Lm
    old = json.loads(PARAMS['refined'].read_text()); p = old['profiles']['1']; var = json.loads(PARAMS['variants'].read_text())['variants']
    scale = np.interp(np.log(np.maximum(r / RS, 1e-5)), p['lnr_centres'], p['robust_contrast']).astype('float32')
    layers = {'01': ((2, 4, 8, 16, 32), 'refined:achf', 3.), '04': ((1, 2, 4, 8, 16), 'variants:micro1_16', 1.5), '05': ((2, 4, 8, 16, 32, 48), 'variants:fi2_48', 3.), '06': ((4, 8, 16, 32, 64), 'variants:estructura4_64', 3.)}
    acc = {k: np.zeros((H, W), np.float32) for k in layers}; w = good.astype(np.float32)
    for sig in sorted(set(s for v_ in layers.values() for s in v_[0])):
        band = x - (normgauss1(x, w, sig) if A.ordre == 1 else normgauss(x, w, sig))
        for k, v_ in layers.items():
            if sig in v_[0]: acc[k] += band / len(v_[0])
        log(f'  σ {sig}')
    sigmamap = np.load(PARAMS['sigma'], mmap_mode='r'); wsup = m.astype('float32'); ctx = h1_setup(r, m)
    for k, (sigmas, ts, se) in layers.items():
        d = np.where(good, acc[k] / scale, 0).astype('float32'); kind, key = ts.split(':'); sc = old['filters'][key]['scale_tanh'] if kind == 'refined' else var[key]['scale_tanh']
        mapped = (.5 * np.tanh(d / max(sc, 1e-6))).astype('float32'); sm = sn_smooth(mapped, m, sigmamap); centered, hist = centre_rings(sm, m, r)
        aa = np.clip(.5 + centered, 0, 1); aa[~m] = .5; den = gauss(wsup, se); b = .5 + gauss((aa - .5) * wsup, se) / np.maximum(den, 1e-8); b[~m] = .5
        desa(k, b, extra=dict(sigmas=sigmas, scale_tanh=sc, external_sigma=se, entrada='ln lluminància (R+2G+B)/4, perfil de contrast del canal G', H1=h1(b, m, ctx)['worst']))
        del d, mapped, sm, centered, aa, b; gc.collect()
elif ETAPA == 'E4':  # ACHF angular 03 / 03v30 / 07 (47, 48, 49): pas alt al llarg de l'arc a cada tren (V42/V88, sense a4v)
    old = json.loads(PARAMS['gran'].read_text()); profiles = old['post_contrast_profiles']; mv = np.load(PARAMS['vixen_support']); ms = np.load(PARAMS['sony_support'])
    z4 = np.load(PARAMS['s4_npz']); y0, y1, x0, x1 = z4['box'].astype(int); mv[y0:y1, x0:x1] |= np.load(PARAMS['s4_sup'])
    V = np.array(np.load(FONTS / 'vixen_starless.npy', mmap_mode='r')[..., 1]); V[BOXQ] = Q['V']; SS = np.load(FONTS / 'sony_starless.npy', mmap_mode='r')[..., 1]
    mv[BOXQ] = DOMQ; ms[BOXQ] &= DOMQ & ~Q['dins_franja']
    masks = {'vixen': mv & np.isfinite(V) & (V > 0), 'sony': ms & np.isfinite(SS) & (SS > 0)}; mm = masks['vixen'] | masks['sony']
    wv = np.load(PARAMS['weight_vixen']); wv = np.where(masks['sony'], wv, masks['vixen'].astype('float32')) * masks['vixen']; ws = (1 - wv) * masks['sony']
    sigmamap = np.load(PARAMS['sigma'], mmap_mode='r'); bands = {}; keys = {'03': 0., '03v30': 4., '07': 8.}
    for tag, src, mask in (('vixen', V, masks['vixen']), ('sony', SS, masks['sony'])):
        p_, valid, r0, nt = (angular_polar1(np.log(np.maximum(np.asarray(src), 1e-8)), mask, r, t, CX, CY) if A.ordre == 1 else angular_polar(np.log(np.maximum(np.asarray(src), 1e-8)), mask, r, t))   # V98: ordre 1 al llarg de l'arc
        for key, sr in keys.items():
            q = p_ if sr == 0 else gaussian_filter1d(p_ * valid, sr, axis=0, mode='constant', cval=0) / np.maximum(gaussian_filter1d(valid, sr, axis=0, mode='constant', cval=0), 1e-8)
            bands[tag, key] = back(q, mask, r, t, r0, nt).astype('float32')
        del p_, valid, q; gc.collect(); log('polar ' + tag)
    scale = np.zeros((H, W), np.float32)
    for tag, w_ in (('vixen', wv), ('sony', ws)):
        pr = profiles[tag]; scale += w_ * np.interp(np.log(np.maximum(r / RS, 1e-5)), pr['lnr_centres'], pr['robust_contrast']).astype('float32')
    ctx = h1_setup(r, mm)
    for key, sr in keys.items():
        d = wv * bands['vixen', key] + ws * bands['sony', key]; d = np.where(mm, d / np.maximum(scale, .002), 0).astype('float32')
        mapped = (.5 * np.tanh(d / old['scale_tanh'])).astype('float32'); sm = sn_smooth(mapped, mm, sigmamap); centered, hist = centre_rings(sm, mm, r)
        aa = np.clip(.5 + centered, 0, 1); aa[~mm] = .5
        desa(key, aa, alfa=alfa_domini(mm, fosa=4.0), extra=dict(sigma_radial=sr, fosa_alfa_vora_px=4.0, H1=h1(aa, mm, ctx)['worst']))   # V98 (d14): a l'extrem de l'arc el pas alt no té suport a banda i banda
desa_json(f'F3_{ETAPA}.json', rep); log('ETAPA ' + ETAPA + ' COMPLETA')

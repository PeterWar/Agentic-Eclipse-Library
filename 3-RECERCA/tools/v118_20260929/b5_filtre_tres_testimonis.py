"""b5 (V118, 29-09-2026) · FILTRE DE DETALL RADIAL COHERENT AMB TRES TESTIMONIS (Sony A, Sony B i Vixen), AMB LES ENTRADES SENSE ESTRELLES.
Encàrrec de Pere: «fes V118 amb els 3 testimonis, incloent el Vixen i treu les estrelles del filtre, recorda que vam acordar que els filtres
havien d'anar sense estrelles» (acord del 10-09, V42: els filtres, sobre una fusió sense estrelles; les estrelles, a la seva capa de llum mesurada).
Sobre el b1 de la V117 (el mateix nucli: pla log-polar centrat al Sol, detall azimutal G_θ(0,15°) − G_θ(1,5°) de ln L amb suavitzat radial
d'un 1,5 % de r, coherència a la finestra 5 % r × 1°), tres canvis:
  1. TRES TESTIMONIS. D = w₃ · [A, B i V del mateix signe] · signe · min(|D_A|, |D_B|, |D_V|), amb w₃ = min(w_AB, w_AV, w_BV).
     La Vixen té una altra òptica i un altre sensor: rebutja també el que és de la lent de 300 mm (A i B la comparteixen). Fora del camp de la
     Vixen no hi ha tercer testimoni i la capa hi és neutra (la finestra de coherència n'esvaeix la vora).
  2. SENSE ESTRELLES, amb el mètode de la d4 (V114: llum estel·lar empírica restada, sense clonar píxels):
     · Vixen: `vixen_starless.npy` de la d4, que és exactament `flat2d_v5/apilats/vixen_total.npy` menys els seus models;
     · A i B: els models de la d4 de la Sony (ajustats a la Sony combinada) restats de CADA apuntament amb la seva amplitud, ajustada per mínims
       quadrats a la caixa de 65 px amb un fons quadràtic propi (A i B tenen amplituds 0,91–1,05 del model);
     · peu reservat (r < 22 px a la d4; aquí r ≤ 25 px a totes les posicions de les tres llistes, més `star_footprints` dilatat 3 px): fora
       del suport. La d4 no hi afirma cap detall de corona, i el filtre hi és neutre.
     · HALO: els models de la d4 només en treuen el nucli; l'halo de les brillants (fins a ~50 px a la V 6,8 de 2,7 R☉) el veuen els tres
       testimonis i passaria. Dues passades: amb el peu de 25 px es mesura, al detall de CADA testimoni, fins on l'halo aixeca el detall per
       sobre del fons de 100–130 px (radis_halo; les dues de V ≤ 6,5, 206 px), i la segona passada exclou cada estrella fins a aquest radi.
  3. La Vixen, igualada abans a la resolució de la Sony (8,3″ contra 5,5″, mesura del 16-08): gaussiana de σ = 1,23 px (com el b4).
Funcions reutilitzables: entrades() i nucli3(). Ús: b5_filtre_tres_testimonis.py <carpeta_sortida>
  → D_minim_f32.npy (el detall concordant de tres, cartesià, amb el nom que esperen b25 i b3), W3_coherencia_f16.npy, DA/DB/DV_f16.npy, B5_REBUT.json"""
import sys, json, time, glob, hashlib, importlib.util, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
AQUI = Path(__file__).resolve().parent; R = AQUI.parents[2]
spec = importlib.util.spec_from_file_location('b1', R / '3-RECERCA/tools/v117_20260929/b1_filtre_coherent_AB.py'); b1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b1)
H, W, SOL, RS = b1.H, b1.W, b1.SOL, b1.RS
AP = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'; S4 = R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources'
ESCALA = 946.0 / RS; SIG_V = float(np.sqrt(8.3 ** 2 - 5.5 ** 2) / 2.355 / ESCALA); R_PEU = 25
def llum(t, fw=None):
    """lluminància (R + 2G + B)/4 TAL QUAL i suport (canals finits i > 0; den > 0 si n'hi ha)."""
    L = np.zeros((H, W), np.float32); m = np.zeros((H, W), bool); d = np.load(fw, mmap_mode='r') if fw else None
    for y0 in range(0, H, 1024):
        s = slice(y0, min(H, y0 + 1024)); a = np.asarray(t[s], np.float32)
        L[s] = (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4; m[s] = np.all(np.isfinite(a) & (a > 0), axis=2)
        if d is not None: m[s] &= np.asarray(d[s]) > 0
    return np.where(m, L, 0).astype(np.float32), m
def posicions():
    return sorted({tuple(int(v) for v in np.load(f)['xy']) for pat in ('sony_star_*.npz', 'vixen_star_*.npz', 'fusion_star_*.npz') for f in glob.glob(str(S4 / pat))})
_yy, _xx = np.mgrid[0:65, 0:65].astype(np.float32); _u, _v = (_xx - 32) / 32, (_yy - 32) / 32
_BQ = np.stack([np.ones_like(_u), _u, _v, _u * _u, _u * _v, _v * _v], -1).reshape(-1, 6)
def treu_sony(L, m):
    """resta de L (in situ) els models de la d4 de la Sony, cadascun amb l'amplitud s ≥ 0 ajustada a aquest apuntament (fons quadràtic propi),
    en ordre, com la d4 (sobre el resultat de l'anterior). Torna la llista d'ajustos."""
    out = []
    for f in sorted(glob.glob(str(S4 / 'sony_star_*.npz'))):
        z = np.load(f); x, y = (int(v) for v in z['xy']); c = z['component'].astype(np.float32); M = (c[..., 0] + 2 * c[..., 1] + c[..., 2]) / 4
        if x < 32 or y < 32 or x + 33 > W or y + 33 > H: out.append(dict(xy=[x, y], nota='fora del llenç')); continue
        ys, xs = slice(y - 32, y + 33), slice(x - 32, x + 33); P = L[ys, xs]; ok = m[ys, xs]
        if ok.mean() < 0.5: out.append(dict(xy=[x, y], nota='fora del suport')); continue
        A_ = np.concatenate([M.reshape(-1, 1), _BQ], 1)[ok.ravel()]; cf = np.linalg.lstsq(A_, P[ok], rcond=None)[0]; s = float(max(cf[0], 0.0))
        bg = (_BQ @ cf[1:]).reshape(65, 65); nou = P - s * M
        rr = np.hypot(_xx - 32, _yy - 32); anell = ok & (rr > 22) & (rr < 32); nucli = ok & (rr < 4)
        sd = float(np.std((nou - bg)[anell])) if anell.sum() > 50 else np.nan
        dolent = ok & (nou <= 0.2 * np.maximum(P, 1e-9)); m[ys, xs] &= ~dolent; L[ys, xs] = np.where(m[ys, xs], nou, 0)
        out.append(dict(xy=[x, y], s=round(s, 4), pic_model=round(float(M.max()), 2),
                        residu_nucli_sobre_pic=round(float(np.mean((nou - bg)[nucli]) / max(M.max(), 1e-9)), 4) if nucli.any() else None,
                        residu_nucli_en_sigma=round(float(np.mean((nou - bg)[nucli]) / sd), 2) if nucli.any() and np.isfinite(sd) and sd > 0 else None))
    return out
def entrades(radis=None):
    """LA, LB (Sony, sense estrelles), LV (Vixen sense estrelles, a la resolució de la Sony) i el suport comú m (sense la taca de l'eix d'A ni els peus).
    radis: {(x, y): r} de l'halo mesurat per radis_halo(); per defecte, R_PEU."""
    # com b1.suport(), però els models es resten sobre la dada SENCERA (amb el nucli de l'estrella) i el peu s'exclou després
    LA, mA = b1.llum(b1.F['A'], b1.F['Aw']); LB, mB = b1.llum(b1.F['B'], b1.F['Bw'])
    fitA = treu_sony(LA, mA); fitB = treu_sony(LB, mB)
    yy_, xx_ = np.ogrid[:H, :W]; mA &= np.hypot(xx_ - b1.GX, yy_ - b1.GY) > 320
    LV, mV = llum(np.load(S4 / 'vixen_starless.npy', mmap_mode='r'), AP / 'vixen_den.npy')
    g = lambda x: cv2.GaussianBlur(x, (0, 0), SIG_V)
    LV = np.where(mV, g(np.where(mV, LV, 0).astype(np.float32)) / np.maximum(g(mV.astype(np.float32)), 1e-6), 0).astype(np.float32)
    peu = ndi.binary_dilation(np.asarray(np.load(S4 / 'star_footprints.npy', mmap_mode='r')) > 0, iterations=3); pos = posicions()
    for x, y in pos:
        rp = int((radis or {}).get((x, y), R_PEU)); y0, y1, x0, x1 = max(0, y - rp), min(H, y + rp + 1), max(0, x - rp), min(W, x + rp + 1)
        yy, xx = np.ogrid[y0:y1, x0:x1]; peu[y0:y1, x0:x1] |= (xx - x) ** 2 + (yy - y) ** 2 <= rp ** 2
    m = mA & mB & ndi.binary_erosion(mV, iterations=4) & ~peu
    return LA, LB, LV, m, dict(ajust_A=fitA, ajust_B=fitB, estrelles_amb_peu=len(pos), px_peu=int(peu.sum()), sigma_vixen_px=round(SIG_V, 3))
ANELLS = [26, 32, 40, 50, 64, 80, 100]; BASE = (100, 130); Q_HALO = 1.3; MARGE = 6; V_BRILLANT, R_BRILLANT = 6.5, 206
def radis_halo(Dc, pos):
    """radi de l'halo de cada estrella, mesurat al detall de CADA testimoni (abans de la concordança; Dc = [D_A, D_B, D_V] cartesians):
    anells des de 26 px; q = mitjana dels tres de rms(anell) / rms(100–130 px); el radi és la vora exterior de l'últim anell consecutiu amb
    q > 1,3, més 6 px de marge (com a mínim R_PEU; com a molt 106). Sense fons mesurable (fora del suport comú), R_PEU.
    Control nul (29-09): a 332 posicions sense estrella, el 6,3 % en surt amb radi > 25 px (les estrelles: el 71 %).
    Les dues més brillants (V ≤ 6,5, totes dues a més de 6,9 R☉) tenen un halo que passa de 130 px i en contamina el fons: la de 6,9 R☉ el
    té mesurat fins a 200 px contra el mateix anell girat 8–12° al voltant del Sol. Tenen R_BRILLANT (206 px). Aquesta referència girada
    no serveix per a totes: a 3–6 R☉ els raigs canvien amb l'angle i el control nul hi dona un 39 % de falsos positius."""
    yy, xx = np.mgrid[-BASE[1]:BASE[1] + 1, -BASE[1]:BASE[1] + 1]; rq = np.hypot(xx, yy); out = {}; det = {}
    cat = json.load(open(R / '4-RESULTATS/v114_estrelles_20260928/CATALEG_ACCEPTAT_V114.json'))['stars']
    brill = [(s_['x'], s_['y']) for s_ in cat if s_['V'] <= V_BRILLANT]
    for x, y in pos:
        if any(np.hypot(x - bx, y - by) < 8 for bx, by in brill): out[(x, y)] = R_BRILLANT; det[f'{x},{y}'] = dict(radi=R_BRILLANT, regla=f'V ≤ {V_BRILLANT}'); continue
        if x < BASE[1] or y < BASE[1] or x + BASE[1] >= W or y + BASE[1] >= H: continue
        Ps = [np.asarray(D[y - BASE[1]:y + BASE[1] + 1, x - BASE[1]:x + BASE[1] + 1], np.float32) for D in Dc]
        def rms(P, a, b):
            k = (rq >= a) & (rq < b) & (P != 0); return float(np.sqrt(np.mean(P[k] ** 2))) if k.sum() > 40 else np.nan
        base = [rms(P, *BASE) for P in Ps]
        if not all(np.isfinite(base)) or min(base) <= 0: continue
        r_ = R_PEU; qs = []
        for a, b in zip(ANELLS[:-1], ANELLS[1:]):
            v = [rms(P, a, b) / bs for P, bs in zip(Ps, base)]; v = [u for u in v if np.isfinite(u)]
            q = float(np.mean(v)) if v else np.nan; qs.append(round(q, 2) if np.isfinite(q) else None)
            if not np.isfinite(q) or q <= Q_HALO: break
            r_ = b + MARGE
        out[(x, y)] = int(r_); det[f'{x},{y}'] = dict(radi=int(r_), q_anells=qs)
    return out, det
def nucli3(LA, LB, LV, m):
    """el filtre de tres testimonis al pla log-polar: torna PM, DA, DB, DV, w3, D3 (i les tres coherències per parelles)."""
    PM = b1.polar(m.astype(np.float32)) > 0.999; den_c = {}
    def gn(x, sr, st_):
        if (sr, st_) not in den_c: den_c[(sr, st_)] = b1.gcv(PM.astype(np.float32), sr, st_)
        den = den_c[(sr, st_)]; return b1.gcv(np.where(PM, x, 0).astype(np.float32), sr, st_) / np.maximum(den, 1e-6), den
    def detall(L):
        x = np.where(PM, np.log(np.maximum(b1.polar(L), 1e-9)), 0).astype(np.float32); a, _ = gn(x, b1.SR, b1.S1); c, _ = gn(x, b1.SR, b1.S2)
        return np.where(PM, a - c, 0).astype(np.float32)
    DA, DB, DV = detall(LA), detall(LB), detall(LV)
    def coh(u, v):
        cov, den = gn(u * v, b1.WR, b1.WT); vu, _ = gn(u * u, b1.WR, b1.WT); vv, _ = gn(v * v, b1.WR, b1.WT)
        w = np.clip(cov / np.maximum(0.5 * (vu + vv), 1e-12), 0, 1).astype(np.float32); w[~PM] = 0; return w * np.clip((den - 0.6) / 0.4, 0, 1).astype(np.float32)
    wp = {'A·B': coh(DA, DB), 'A·V': coh(DA, DV), 'B·V': coh(DB, DV)}
    w3 = np.minimum(np.minimum(wp['A·B'], wp['A·V']), wp['B·V'])
    mag = np.minimum(np.minimum(np.abs(DA), np.abs(DB)), np.abs(DV)); igual = (DA * DB > 0) & (DA * DV > 0)
    D3 = (w3 * np.where(igual, np.sign(DA) * mag, 0)).astype(np.float32)
    return PM, DA, DB, DV, w3, D3, wp
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()
if __name__ == '__main__':
    t0 = time.time(); OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
    # passada 1: peu fix de 25 px, per mesurar l'halo de cada estrella al detall de cada testimoni
    LA, LB, LV, m, info = entrades(); print(f'entrades {time.time() - t0:.0f}s · suport comú {m.mean():.3f} · peus {info["px_peu"]} px', flush=True)
    PM, DA, DB, DV, w3, D3, wp = nucli3(LA, LB, LV, m); del LA, LB, LV
    radis, det_halo = radis_halo([b1.cart(DA), b1.cart(DB), b1.cart(DV)], posicions()); del PM, DA, DB, DV, w3, D3, wp
    print(f'halo {time.time() - t0:.0f}s · estrelles amb radi > {R_PEU} px: {sum(v > R_PEU for v in radis.values())} de {len(radis)} mesurables', flush=True)
    # passada 2: el peu de cada estrella, fins on arriba el seu halo
    LA, LB, LV, m, info = entrades(radis); print(f'entrades 2 {time.time() - t0:.0f}s · suport comú {m.mean():.3f} · peus {info["px_peu"]} px', flush=True)
    PM, DA, DB, DV, w3, D3, wp = nucli3(LA, LB, LV, m); del LA, LB, LV
    print(f'filtre {time.time() - t0:.0f}s', flush=True)
    viu = ~m & ~ndi.binary_dilation(m, iterations=2)
    c = b1.cart(D3); c[viu] = 0; np.save(OUT / 'D_minim_f32.npy', c.astype(np.float32))
    np.save(OUT / 'W3_coherencia_f16.npy', b1.cart(w3).astype(np.float16))
    for nom, P in (('DA', DA), ('DB', DB), ('DV', DV)): np.save(OUT / f'{nom}_f16.npy', b1.cart(P).astype(np.float16))
    rR = (np.exp(b1.rho) / RS)[:, None]; bandes = {}
    for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5), (5.5, 9.5)):
        k = PM & (rR >= a) & (rR < b)
        if k.sum() < 1000: bandes[f'{a}-{b}'] = dict(px=int(k.sum())); continue
        bandes[f'{a}-{b}'] = dict(coincidencia_mediana={**{p: round(float(np.median(v[k])), 3) for p, v in wp.items()}, 'tres (mínim)': round(float(np.median(w3[k])), 3)},
                                  sd_detall_pct={n: round(float(X[k].std() * 100), 3) for n, X in (('A', DA), ('B', DB), ('V', DV))}, sd_D3_pct=round(float(D3[k].std() * 100), 3))
    fa = [f for f in info['ajust_A'] if 's' in f]; fb = [f for f in info['ajust_B'] if 's' in f]
    res = lambda L: [round(float(np.nanpercentile([f['residu_nucli_en_sigma'] for f in L if f['residu_nucli_en_sigma'] is not None], q)), 2) for q in (10, 50, 90)]
    rep = dict(guio=str(Path(__file__).relative_to(R)), base='3-RECERCA/tools/v117_20260929/b1_filtre_coherent_AB.py (nucli, geometria, taca de l\'eix)',
               entrades=dict(A=str(b1.F['A'].relative_to(R)), B=str(b1.F['B'].relative_to(R)), V_sense_estrelles=str((S4 / 'vixen_starless.npy').relative_to(R)),
                             models_sony=str(S4.relative_to(R)) + '/sony_star_*.npz'),
               combinacio='D = min(w_AB, w_AV, w_BV) · [A, B i V del mateix signe] · signe · min(|D_A|, |D_B|, |D_V|)',
               estrelles=dict(metode='models de la d4 restats (A i B amb amplitud pròpia i fons quadràtic); Vixen: vixen_starless de la d4; peu r ≤ 25 px fora del suport',
                              estrelles_amb_peu=info['estrelles_amb_peu'], px_peu=info['px_peu'],
                              A=dict(restades=len(fa), s_p10_p50_p90=[round(float(np.percentile([f['s'] for f in fa], q)), 3) for q in (10, 50, 90)], residu_nucli_sigma_p10_p50_p90=res(fa)),
                              B=dict(restades=len(fb), s_p10_p50_p90=[round(float(np.percentile([f['s'] for f in fb], q)), 3) for q in (10, 50, 90)], residu_nucli_sigma_p10_p50_p90=res(fb))),
               sigma_vixen_px=info['sigma_vixen_px'], suport_comu=float(m.mean()), bandes=bandes, segons=round(time.time() - t0, 1))
    rep['estrelles']['halo'] = dict(criteri=f'q = rms(anell)/rms(100–130 px) del detall de cada testimoni, mitjana dels tres; radi = vora de l\'últim anell amb q > {Q_HALO} + {MARGE} px; V ≤ {V_BRILLANT}: {R_BRILLANT} px; control nul: 6,3 % de 332 posicions sense estrella',
                                    mesurables=len(radis), amb_radi_mes_gran=sum(v > R_PEU for v in radis.values()), radis_mes_grans=sorted([v for v in radis.values() if v > R_PEU], reverse=True))
    (OUT / 'B5_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    (OUT / 'B5_AJUSTOS_ESTRELLES.json').write_text(json.dumps(dict(A=info['ajust_A'], B=info['ajust_B'], halo=det_halo), ensure_ascii=False, indent=0))
    (OUT / 'B5_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False, indent=1))

"""Pas 4: moviments de la corona durant la totalitat, amb els fotogrames de la Vixen (VSD90SS + R6 III).

La Vixen va repetir l'escala d'exposicions (1/2000–1/2 s i 1/1000–1 s) quatre vegades: poc després de C2 i
entre C2+68 i C2+92 s.  Cada escala és una «època»: un HDR de 6 fotogrames presos en ~5 s.

Ús: python p4_moviment.py [etapa]   etapes: epoques (per defecte, amb cau), mesura, anima

Cadena:
1. calibració de cada CR3: (cru − fosc de la seva exposició) / flat radial; saturació al cru (85 % del rang lineal);
   verd a resolució completa (quincunx interpolat, cap desbayerat de color);
2. cada fotograma al marc del Sol (centre del Sol del manifest validat, ≤ 0,09 px) i HDR de l'època
   (pes = exposició; fora la saturació i la Lluna de cada fotograma);
3. igualació fotomètrica entre èpoques (el Sol es pon: la corona baixa un ~5 % en un minut);
4. passa-alt en logaritme i mesura de desplaçaments per finestres, amb controls:
   parells nuls (6 s), velocitat del sensor (tot el que és fix al sensor es mou amb la deriva) i de la Lluna;
5. animació GIF/MP4 només amb èpoques reals (cap fotograma interpolat) i fletxes als moviments confirmats.
"""
import sys, csv, json, time, numpy as np, cv2
from comu import *
from ael import calibrate as cal, motion, annotate, io as aio, render

ETAPA = sys.argv[1] if len(sys.argv) > 1 else 'tot'
RAW = ARREL / '0-RAW/Vixen R6III/Vixen Fase totalitat'
MD = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/calibration_VIXEN/0-calibracio'
MAN = ARREL / '4-RESULTATS/derivats/Vixen/Corona_HDR_Vixen/manifest.csv'
RM = RES / 'moviment'; RM.mkdir(exist_ok=True)
OM = OUT / 'moviment'; OM.mkdir(exist_ok=True)
MARGE = (172.0, 108.0)          # manifest (àrea visible) → sensor sencer
R_SOL = 959.0 / 2.1495          # 446,15 px
R_LLUNA = 462.0                 # px (recerca 75 §6: 460; +2 de marge de vora)
ESCALA = 2.1495                 # ″/px
CANVAS = (3000, 3000); REF = (1500.0, 1500.0)
POU, PED = 16383.0, 511.5
EPOQUES = {                      # noms de fitxer (sense 572A ni .CR3)
    'E1': range(2967, 2973), 'E1b': range(2973, 2979), 'E2': range(2985, 2991),
    'E2b': range(2991, 2997), 'E3': range(2997, 3003), 'E4': range(3003, 3009)}

man = {r['nom']: r for r in csv.DictReader(open(MAN))}
_darks = {}
def fosc(exp):
    fitxers = sorted((MD / 'masters_dark').glob('MD_E*s.fits'))
    vals = {float(f.name[4:-6]): f for f in fitxers}
    k = min(vals, key=lambda v: abs(np.log(v / exp)))
    assert abs(np.log(k / exp)) < 0.04, (exp, k)   # 10,3 s reals = 10 s nominals (EXIF) al fosc
    if k not in _darks:
        _darks[k] = cal.load_calibration_frame(vals[k])
    return _darks[k]
FLAT = None

import os
VERSIO = os.environ.get('AEL_MOV_VERSIO', 'v2')     # v1: flat radial; v2: flat radial × PRNU fi (recerca 90)
def carrega(nm):
    global FLAT
    if FLAT is None:
        FLAT = cal.load_calibration_frame(MD / 'FLAT_RADIAL.fits')
        if VERSIO != 'v1':
            pr = np.load(RM / 'PRNU_VIXEN_FINE_mosaic_visible.npy')
            full = np.ones_like(FLAT)
            full[int(MARGE[1]):int(MARGE[1]) + pr.shape[0], int(MARGE[0]):int(MARGE[0]) + pr.shape[1]] = pr
            FLAT = (FLAT * full).astype(np.float32)
    r = man[nm]
    exp = float(r['exp_s'])
    info = cal.read_raw(RAW / nm, full=True)
    sat = cal.saturation_mask(info['bayer'], POU, PED, 0.85)
    c = cal.calibrate(info['bayer'], fosc(exp), FLAT)
    g, bad = cal.green_plane(c, info['pattern'], sat)
    return motion.Frame(name=nm, t=float(r['t_rel_c2']), exposure=exp,
                        sun_xy=(float(r['sol_x']) + MARGE[0], float(r['sol_y']) + MARGE[1]),
                        moon_xy=(float(r['lluna_x']) + MARGE[0], float(r['lluna_y']) + MARGE[1]),
                        data=np.where(bad, np.nan, g).astype(np.float32), saturated=bad)

geo_t = EclipseGeometry(shape=CANVAS, sun_xy=REF, sun_radius_px=R_SOL, moon_radius_px=R_LLUNA,
                        north_deg=0.0, arcsec_per_px=ESCALA, note='marc del Sol, orientació del sensor Vixen')

def epoques():
    out = {}
    for nom, rng in EPOQUES.items():
        f = RM / (f'epoca_{nom}.npz' if VERSIO == 'v1' else f'epoca_{nom}_{VERSIO}.npz')
        if f.exists():
            z = np.load(f, allow_pickle=True)
            e = motion.Epoch(name=nom, t=float(z['t']), t_min=float(z['t_min']), t_max=float(z['t_max']),
                             data=z['data'], valid=z['valid'], geometry=EclipseGeometry.from_json(str(z['geo'])),
                             moon_xy=[tuple(m) for m in z['moons']], members=list(z['members']))
            out[nom] = e
            continue
        t0 = time.time()
        frames = [carrega(f'572A{k}.CR3') for k in rng]
        e = motion.merge_epoch(frames, REF, CANVAS, geo_t, sat_dilate=2, moon_margin_px=3.0, name=nom)
        np.savez(f, data=e.data, valid=e.valid, t=e.t, t_min=e.t_min, t_max=e.t_max, geo=e.geometry.to_json(),
                 moons=np.array(e.moon_xy), members=np.array(e.members))
        print(nom, f't={e.t:.1f} s ({e.t_min:.1f}–{e.t_max:.1f})', 'exps', [f.exposure for f in frames],
              f'vàlid {e.valid.mean():.3f}', f'{time.time() - t0:.0f} s')
        out[nom] = e
        del frames
    return out

# velocitats de les falses aparences, al marc del Sol (px/s), del manifest
def velocitats():
    ks = [k for k in man if man[k]['usat'] == 'True']
    t = np.array([float(man[k]['t_rel_c2']) for k in ks])
    sx = np.array([float(man[k]['sol_x']) for k in ks]); sy = np.array([float(man[k]['sol_y']) for k in ks])
    lx = np.array([float(man[k]['lluna_x']) for k in ks]); ly = np.array([float(man[k]['lluna_y']) for k in ks])
    vs = (np.polyfit(t, sx, 1)[0], np.polyfit(t, sy, 1)[0])
    vm = (np.polyfit(t, lx - sx, 1)[0], np.polyfit(t, ly - sy, 1)[0])
    return dict(sensor=(-vs[0], -vs[1]), lluna=vm)

if __name__ == '__main__' and ETAPA in ('tot', 'epoques'):
    t00 = time.time()
    E = epoques()
    V = velocitats()
    print('velocitats al marc del Sol (px/s): sensor', np.round(V['sensor'], 4), 'Lluna', np.round(V['lluna'], 4))
    noms = list(EPOQUES)
    ll = [E[n] for n in noms]
    fot = motion.match_epochs(ll, ref=0, ring_rsun=(1.1, 2.0))
    print('igualació fotomètrica (a, b):', [(d['epoch'], round(d['a'], 4), round(d['b'], 1)) for d in fot])
    json.dump(dict(velocitats=V, fotometria=fot, epoques={n: dict(t=E[n].t, t_min=E[n].t_min, t_max=E[n].t_max,
              membres=E[n].members, valid=float(E[n].valid.mean())) for n in noms}),
              open(RM / 'P4_EPOQUES.json', 'w'), indent=1, default=float)
    print(f'{time.time() - t00:.0f} s')


# ------------------------------------------------------------------------------------------------
# Mesura: grups d'èpoques, passa-banda, vectors, controls
# ------------------------------------------------------------------------------------------------
def combina(eps, nom):
    """Mitjana de diverses èpoques ja igualades (on n'hi ha almenys una)."""
    num = np.zeros(CANVAS, np.float64); den = np.zeros(CANVAS, np.float64)
    for e in eps:
        num[e.valid] += e.data[e.valid]; den[e.valid] += 1
    val = den > 0
    t = float(np.mean([e.t for e in eps]))
    geo = eps[0].geometry
    moons = sum([list(e.moon_xy) for e in eps], [])
    return motion.Epoch(name=nom, t=t, t_min=min(e.t_min for e in eps), t_max=max(e.t_max for e in eps),
                        data=np.where(val, num / np.maximum(den, 1), np.nan).astype(np.float32), valid=val,
                        geometry=geo, moon_xy=moons, members=sum([e.members for e in eps], []))

def passabanda(e, s1=1.0, s2=6.0):
    """ln I passat per G(s1) menys G(s2): detall de 1–6 px, amb convolució normalitzada."""
    from ael.filters import normalized_gaussian
    m = e.valid & np.isfinite(e.data) & (e.data > 0)
    lg = np.where(m, np.log(np.where(m, e.data, 1.0)), np.nan).astype(np.float32)
    a = normalized_gaussian(lg, m, s1, 0.5) if s1 > 0 else lg
    b = normalized_gaussian(lg, m, s2, 0.5)
    return (a - b).astype(np.float32)

def exclou_lluna(eps, marge=10.0):
    yy, xx = np.mgrid[0:CANVAS[0], 0:CANVAS[1]]
    ex = np.zeros(CANVAS, bool)
    for e in eps:
        for (mx, my) in e.moon_xy:
            ex |= np.hypot(xx - mx, yy - my) <= R_LLUNA + marge
    return ex

def _cadena_vectors(E, V, A, B, nuls, *, window=61, step=20, search=26, r_rang=(1.1, 2.2), banda=(2.0, 12.0),
                    marge_lluna=15.0, min_iso=0.3):
    """Una tirada de la cadena: A = (inici, final), B = (inici, final) disjunts de A; nuls = dues parelles
    properes en el temps (una per a cada extrem).  Retorna (info, vectors de A)."""
    s1, s2 = banda
    imgs = {}
    def hp(e):
        if id(e) not in imgs:
            imgs[id(e)] = passabanda(e, s1, s2)
        return imgs[id(e)]
    ex = exclou_lluna([E[n] for n in EPOQUES], marge_lluna)
    kw = dict(window=window, step=step, search=search, r_range_rsun=r_rang, exclude=ex, min_peak=0.6)
    g = A[0].geometry
    mv = lambda a, b: motion.measure_displacements(hp(a), hp(b), np.isfinite(hp(a)), np.isfinite(hp(b)), g, **kw)
    n0, n1 = mv(*nuls[0]), mv(*nuls[1])
    llA, llB = mv(*A), mv(*B)
    dtA, dtB = A[1].t - A[0].t, B[1].t - B[0].t
    afA = motion.fit_global_affine(llA, g.sun_xy, classes=("",))
    afB = motion.fit_global_affine(llB, g.sun_xy, classes=("",))
    sn0, sn1 = motion.null_noise(n0), motion.null_noise(n1)
    soroll = max(sn0['sigma'], sn1['sigma'])
    cls = motion.classify(llA, dtA, sensor_velocity=V['sensor'], moon_velocity=V['lluna'], noise_px=soroll, min_iso=min_iso)
    motion.classify(llB, dtB, sensor_velocity=V['sensor'], moon_velocity=V['lluna'], noise_px=soroll, min_iso=min_iso)
    lim = max(1.5, 3 * soroll)
    c1 = motion.confirm(llA, dtA, null_vecs=n0, null_max_px=lim)
    c2 = motion.confirm(llA, dtA, null_vecs=n1, null_max_px=lim, mid_vecs=llB, dt_mid=dtB, tol_px=1.0, tol_frac=0.25)
    cand = [v for v in llA if v.cls == 'coronal']
    info = dict(dt_s=dtA, dt_independent_s=dtB, afi_global=afA, afi_global_independent=afB,
                soroll_nul=dict(n0=sn0, n1=sn1), limit_nul_px=lim, classes=cls, confirmacio=[c1, c2],
                n_candidats=len(cand), finestra=window, pas=step, cerca=search, r_rsun=r_rang, banda_px=banda,
                marge_lluna_px=marge_lluna, min_iso=min_iso)
    return info, llA

def mesura(E, V, **kw):
    """Tirada real (A = E1 → E3+E4, B = E1b → E2+E2b, cap fotograma comú) i tirada NUL de tota la cadena
    (A = E3 → E4, B = E2 → E2b: 6 s; qualsevol «candidat» hi és un fals positiu)."""
    A1 = combina([E['E3'], E['E4']], 'final'); B1 = combina([E['E2'], E['E2b']], 'final2')
    info, vec = _cadena_vectors(E, V, (E['E1'], A1), (E['E1b'], B1), ((E['E1'], E['E1b']), (E['E3'], E['E4'])), **kw)
    info['parelles'] = dict(A='E1 -> E3+E4', B='E1b -> E2+E2b (cap fotograma comú amb A)', nuls='E1 vs E1b; E3 vs E4')
    infoN, vecN = _cadena_vectors(E, V, (E['E3'], E['E4']), (E['E2'], E['E2b']), ((E['E1'], E['E1b']), (E['E2b'], E['E3'])), **kw)
    infoN['parelles'] = dict(A='E3 -> E4 (6 s)', B='E2 -> E2b (6 s)', nuls='E1 vs E1b; E2b vs E3')
    info['nul_de_cadena'] = infoN
    return info, vec, None, dict(A1=A1, B1=B1)


# ------------------------------------------------------------------------------------------------
# Animació
# ------------------------------------------------------------------------------------------------
GIR_LLENC = 10.6     # graus (antihorari a la pantalla): sensor Vixen → orientació del llenç de Pere (nord 45,25°)

def display_epoca(e, gain, s_fi=(1.0, 8.0), s_gruixut=(2.0, 12.0), r_blend=(1.6, 2.0), perfil=None):
    """Passa-banda en log; la resolució segueix el S/N: fi a prop del limbe, més gruixut enfora.
    ``perfil`` = (r, factor) guany radial comú a totes les èpoques (el mateix per a totes: no altera el moviment)."""
    a = passabanda(e, *s_fi); b = passabanda(e, *s_gruixut)
    rs = e.geometry.rsun_map()
    w = np.clip((rs - r_blend[0]) / (r_blend[1] - r_blend[0]), 0, 1)
    d = np.where(np.isfinite(a) & np.isfinite(b), (1 - w) * a + w * b, np.where(np.isfinite(a), a, b))
    if perfil is not None:
        d = d * np.interp(rs, perfil[0], perfil[1]).astype(np.float32)
    return motion.to_display(d, gain)

def perfil_guany(eps, s_fi=(1.0, 8.0), s_gruixut=(2.0, 12.0), r_blend=(1.6, 2.0), max_guany=3.0, terra=2.0):
    """Guany radial: iguala el contrast del detall amb el de 1,05–1,3 R☉, però mai per sobre de ``max_guany``
    ni per damunt del que permet el soroll (el soroll es mesura com la diferència entre dues èpoques
    properes: RMS(E3 − E4)/√2 a cada anell)."""
    e3, e4 = eps
    def det(e):
        a = passabanda(e, *s_fi); b = passabanda(e, *s_gruixut)
        rs = e.geometry.rsun_map(); w = np.clip((rs - r_blend[0]) / (r_blend[1] - r_blend[0]), 0, 1)
        return (1 - w) * a + w * b
    d3, d4 = det(e3), det(e4)
    rs = e3.geometry.rsun_map()
    rr = np.arange(1.03, 3.3, 0.05); fac = []
    ref = None
    for r0 in rr:
        m = (rs >= r0) & (rs < r0 + 0.05) & np.isfinite(d3) & np.isfinite(d4)
        if m.sum() < 500:
            fac.append(np.nan); continue
        tot = np.sqrt(np.mean(((d3[m] + d4[m]) / 2) ** 2)); soroll = np.std(d3[m] - d4[m]) / 2
        sig = np.sqrt(max(tot ** 2 - soroll ** 2, 0)) + terra * soroll
        if ref is None and r0 >= 1.05:
            ref = sig
        fac.append(sig)
    fac = np.array(fac, float)
    g = np.clip(ref / fac, 1.0, max_guany)
    g = np.where(np.isfinite(g), g, max_guany)
    return (rr + 0.025, g)

def orienta_i_retalla(img01, alt_rsun=2.2, ample_rsun=2.8, sortida=(1320, 1036)):
    M = cv2.getRotationMatrix2D(REF, GIR_LLENC, 1.0)
    rot = cv2.warpAffine(np.nan_to_num(img01, nan=0.0).astype(np.float32), M, CANVAS[::-1], flags=cv2.INTER_CUBIC,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
    h, w = int(round(2 * alt_rsun * R_SOL)), int(round(2 * ample_rsun * R_SOL))
    y0, x0 = int(REF[1] - h / 2), int(REF[0] - w / 2)
    c = np.clip(rot[y0:y0 + h, x0:x0 + w], 0, 1)
    return cv2.resize(c, sortida, interpolation=cv2.INTER_AREA)

def etiqueta(img8, text_sup, text_inf, peu):
    H, W = img8.shape[:2]
    annotate.draw_text(img8, text_sup, (18, 14), size=22, color=(235, 235, 235))
    annotate.draw_text(img8, text_inf, (18, H - 44), size=30, color=(255, 255, 255))
    annotate.draw_text(img8, peu, (W - 18, H - 30), size=18, color=(200, 200, 200), anchor='ra')
    # brúixola: nord a 45,25° a la dreta de la vertical, est 90° en sentit antihorari
    cx, cy, L = W - 70, 80, 42
    for pa, lab in ((0.0, 'N'), (90.0, 'E')):
        a = np.radians(NORD - pa)
        tip = (cx + L * np.sin(a), cy - L * np.cos(a))
        annotate.draw_arrow(img8, (cx, cy), tip, color=(235, 235, 235), width=2, head_len=9, head_width=8)
        annotate.draw_text(img8, lab, (cx + 1.35 * L * np.sin(a), cy - 1.35 * L * np.cos(a)), size=18, anchor='mm')
    return img8

def anima(E, info):
    noms = list(EPOQUES)
    ini = combina([E['E1'], E['E1b']], 'inici'); fi = combina([E['E3'], E['E4']], 'final')
    rs = ini.geometry.rsun_map()
    ref = passabanda(ini, 1.0, 8.0)
    gain = 0.5 / float(np.nanpercentile(np.abs(ref[(rs > 1.05) & (rs < 1.6)]), 99.5))
    perfil = perfil_guany((E['E3'], E['E4']))
    peu = 'Pere Guerra · Agentic Eclipse Library'
    sup = 'Total solar eclipse, 12 Aug 2026 · aligned on the Sun'
    fr6, fr2 = [], []
    for n in noms:
        e = E[n]
        img = annotate.to_rgb8(orienta_i_retalla(display_epoca(e, gain, perfil=perfil)))
        fr6.append(etiqueta(img, sup, f'C2 + {e.t:.0f} s', peu))
    for e, nom in ((ini, 'start'), (fi, 'end')):
        img = annotate.to_rgb8(orienta_i_retalla(display_epoca(e, gain, perfil=perfil)))
        fr2.append(etiqueta(img, sup, f'C2 + {e.t:.0f} s ({nom})', peu))
    d6 = [900] + [450] * (len(fr6) - 1)
    aio.save_gif(OM / 'moviment_6_epoques.gif', fr6, d6)
    aio.save_mp4(OM / 'moviment_6_epoques.mp4', fr6, d6)
    aio.save_gif(OM / 'moviment_parpelleig_inici_final.gif', fr2, [700, 700])
    aio.save_mp4(OM / 'moviment_parpelleig_inici_final.mp4', fr2 * 4, [700, 700] * 4)
    for k, f in enumerate(fr6):
        aio.save_png(OM / f'moviment_epoca_{k + 1}_{noms[k]}.png', f)
    return dict(gain=gain, frames=noms, durades_ms=d6, guany_radial=dict(r_rsun=perfil[0].tolist(), factor=perfil[1].tolist()))

if __name__ == '__main__' and ETAPA in ('tot', 'anima'):
    import pickle
    E = epoques(); noms = list(EPOQUES)
    motion.match_epochs([E[n] for n in noms], ref=0, ring_rsun=(1.1, 2.0))
    V = velocitats()
    info, vec, hp, grups = mesura(E, V)
    a = anima(E, info)
    kmpx = motion.km_per_px(ESCALA, 1.0134)
    cor = [v for v in vec if v.cls == 'coronal']
    info['anima'] = a
    info['km_s_per_px'] = kmpx / info['dt_s']
    info['llindar_deteccio_km_s'] = info['limit_nul_px'] * kmpx / info['dt_s']
    info['candidats'] = [dict(x=v.x, y=v.y, r_rsun=v.r_rsun, residu_px=(v.rdx, v.rdy), km_s=float(np.hypot(v.rdx, v.rdy) * kmpx / info['dt_s']),
                              peak=v.peak, iso=v.iso) for v in cor]
    pickle.dump(dict(info=info, vec=vec), open(RM / 'mesura_final.pkl', 'wb'))
    aio.write_receipt(RM / 'P4_MOVIMENT_REBUT.json', product='coronal motion during totality (Vixen, 6 epochs)',
                      parameters=info, outputs={k: str(OM / k) for k in ('moviment_6_epoques.gif', 'moviment_parpelleig_inici_final.gif')},
                      notes='Vectors: classes sensor/lunar/still/aperture/coronal; coronal confirmats amb nuls locals i testimoni independent.')
    print(json.dumps({k: info[k] for k in ('classes', 'confirmacio', 'llindar_deteccio_km_s', 'candidats', 'anima')}, indent=1, default=float))

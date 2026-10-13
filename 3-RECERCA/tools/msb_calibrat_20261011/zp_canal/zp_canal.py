"""Punts zero per canal (R, G, B) del Vixen + R6 III i factor B/B☉ per canal.

Tasca msb_calibrat_20261011/zp_canal (11-10-2026). Mateix mètode que la cadena
original (còpies a original/xmatch/): cog2.py (corba de creixement, normalitzada a
r = 10 px, plateau r = 14–18), zp.py (obertura r = 7 px, massa d'aire de Kasten i
Young amb skyfield, refracció 20 °C i 930 mbar), zp2.py (model «ZP + k + color»
reparametritzat a X☉, retall 2,5σ, 6 iteracions) i corona2.py (factor al Sol):

    V − m_c = ZP_c − k_c (X − X☉) − c_c (B−V)
    F☉,c   = 10^(0,4 (ZP_c + 26,75 − 0,653 c_c))
    fac_c  = π R☉,px² / F☉,c        [B/B☉ per ADU/s i píxel del canal c]

Afegit respecte de l'original (res no canvia cap número del verd):
- covariància sencera del wls, i σ(ZP − 0,653 c) amb el terme creuat;
- CONTROL OBLIGATORI predeclarat: el verd ha de donar ZP = +14,2052 ± 0,040 i
  fac = 2,7714e-11 a l'1 %. Si no, s'atura (codi de sortida 3) i no escriu cap
  ZP_CANAL.json;
- controls nuls: residus contra (B−V) (pendent, terme quadràtic, Spearman) i
  permutació del (B−V) entre estrelles (2.000, llavor 20261011);
- jackknife per estrelles (deixant-ne una fora i repetint tot l'ajust amb retall);
- variants de sensibilitat: «natiu» (píxels CFA i factor d'àrea), conjunt
  d'estrelles del verd imposat, només V d'Hipparcos, sense terme de color.

Sortida: ../../resultats/msb_calibrat_20261011/zp_canal/ZP_CANAL.json i
ZP_CANAL_rebut.json (sha256 de cada entrada). Taula per estrella a work/canal/.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "original"))
import comu  # noqa: E402
os.chdir(comu.work("xmatch"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402
from skyfield.api import load, wgs84, Star  # noqa: E402

ARREL = comu.ARREL                               # .../4-Photoshop
RES = ARREL / "3-RECERCA/resultats/msb_calibrat_20261011/zp_canal"
CANAL = comu.work("canal")
BV_SOL = 0.653
M_SOL = -26.75
RSUN_AS = 947.07
RAP = 7            # zp.py RAP['r6']
RAP_NORM = 10      # cog2.py, r6
EPOCH = (2026, 8, 12, 18, 29, 18.6)
TEMP, PRES = 20.0, 930.0
SEED = 20261011
NPERM = 2000
# Control predeclarat (zp2.json i corona2.csv del 17-08, Resultats_acceptacio_2026-08-17)
REF_G = dict(ZPsun=14.205187804093502, eZPsun=0.040036052997991955, k=0.7233800430535555,
             c=0.14879704521968498, n=14, fac=2.7714444383608502e-11, fac_nocolor=2.534197091332231e-11)
TOL_FAC = 0.01


def sha256(p, bloc=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bloc)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ARREL))
    except ValueError:
        return str(p)


def kasten_young(alt_deg):
    a = np.asarray(alt_deg, float)
    return 1.0/(np.sin(np.radians(a)) + 0.50572*(a + 6.07995)**(-1.6364))


def airmass(tab):
    """Còpia de zp.py:airmass_of per al R6, i X del Sol."""
    ts = load.timescale()
    eph = comu.efemeride()
    lloc = eph['earth'] + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)
    t = ts.utc(*EPOCH)
    cat = pd.read_csv('cat2_r6.csv')
    key = cat.set_index('TYC')
    alt = []
    for tyc in tab.TYC:
        r = key.loc[tyc]
        st = Star(ra_hours=float(r._RAJ2000)/15., dec_degrees=float(r._DEJ2000))
        ap = lloc.at(t).observe(st).apparent()
        a, _, _ = ap.altaz(temperature_C=TEMP, pressure_mbar=PRES)
        alt.append(a.degrees)
    alt = np.array(alt)
    aps = lloc.at(t).observe(eph['sun']).apparent()
    salt, _, _ = aps.altaz(temperature_C=TEMP, pressure_mbar=PRES)
    return alt, kasten_young(alt), float(kasten_young(salt.degrees)), float(salt.degrees)


def wls(A, y, clip=2.5, nit=6, ok0=None):
    """Còpia de zp2.py:wls; torna també la covariància sencera."""
    ok = np.ones(len(y), bool) if ok0 is None else ok0.copy()
    for _ in range(nit):
        s, *_ = np.linalg.lstsq(A[ok], y[ok], rcond=None)
        r = y - A@s
        sd = 1.4826*np.median(np.abs(r[ok]-np.median(r[ok])))
        new = np.abs(r-np.median(r[ok])) < clip*max(sd, 0.02)
        if (new == ok).all():
            break
        ok = new
    s, *_ = np.linalg.lstsq(A[ok], y[ok], rcond=None)
    r = y[ok]-A[ok]@s
    n, p = ok.sum(), A.shape[1]
    s2 = (r**2).sum()/max(n-p, 1)
    cov = s2*np.linalg.pinv(A[ok].T@A[ok])
    return s, np.sqrt(np.abs(np.diag(cov))), ok, float(np.sqrt(s2)), cov


def fit_fixed(A, y, ok):
    """Mínims quadrats sobre un conjunt fix (sense retall), amb covariància."""
    s, *_ = np.linalg.lstsq(A[ok], y[ok], rcond=None)
    r = y[ok]-A[ok]@s
    n, p = ok.sum(), A.shape[1]
    s2 = (r**2).sum()/max(n-p, 1)
    cov = s2*np.linalg.pinv(A[ok].T@A[ok])
    return s, cov, float(np.sqrt(s2))


def minst_from_phot(path, tab):
    """cog2.py + zp.py: combinació per temps d'exposició, correcció d'obertura r=7 → plateau."""
    z = np.load(path, allow_pickle=True)
    F = z['F']
    exp = z['exp']
    W = exp[:, None, None]
    with np.errstate(invalid='ignore', divide='ignore'):
        Fc = np.nansum(F*W, axis=0)/np.nansum(np.where(np.isfinite(F), W, 0), axis=0)
        br = np.argsort(-tab.flux.values)[:10]
        ref = np.nanmedian(Fc[br]/Fc[br, RAP_NORM-1][:, None], axis=0)
        plateau = np.nanmedian(ref[13:18])
        corr = ref[RAP-1]/plateau
        flux = Fc[:, RAP-1]/corr
        minst = -2.5*np.log10(np.where(flux > 0, flux, np.nan))
    nfr = np.isfinite(F[:, :, RAP-1]).sum(axis=0)
    return dict(minst=minst, flux=flux, apcorr=float(1/corr), plateau=float(plateau),
                cog=ref.tolist(), nframes=nfr)


def sol_factor(ZP, c, cov3, Rsun_px):
    """F☉ i fac amb σ de la covariància (ZP, k, c): a = (1, 0, −0,653)."""
    a = np.array([1.0, 0.0, -BV_SOL])
    msun = ZP - BV_SOL*c
    sig = float(np.sqrt(a@cov3@a))
    Fsun = 10**(0.4*(msun - M_SOL))
    fac = np.pi*Rsun_px**2/Fsun
    return dict(m_sol=float(msun), sigma_m_sol=sig, F_sol_ADU_s=float(Fsun), fac=float(fac),
                sigma_fac_rel=float(0.4*np.log(10)*sig), sigma_fac=float(fac*0.4*np.log(10)*sig))


def null_controls(y, BV, dX, ok, s, rng, A):
    """Controls nuls sobre els residus contra (B−V)."""
    res_all = y - A@s
    r = res_all[ok]
    b = BV[ok]
    out = {}
    # (1) pendent residual contra B−V (zero per construcció en el conjunt ajustat; es dona com a comprovació)
    sl = stats.linregress(b, r)
    out['pendent_residu_vs_BV_estrelles_usades'] = dict(pendent=float(sl.slope), sigma=float(sl.stderr),
                                                        nota='zero per construcció (MQO amb terme lineal)')
    # (1b) amb totes les estrelles amb fotometria (també les retallades)
    fin = np.isfinite(res_all)
    sl2 = stats.linregress(BV[fin], res_all[fin])
    out['pendent_residu_vs_BV_totes'] = dict(pendent=float(sl2.slope), sigma=float(sl2.stderr), n=int(fin.sum()))
    # (2) terme quadràtic: s'afegeix (B−V)² al mateix conjunt d'estrelles
    A2 = np.column_stack([A, -(BV**2)])
    s2, cov2, rms2 = fit_fixed(A2, y, ok)
    e2 = np.sqrt(np.diag(cov2))
    out['terme_quadratic_BV2'] = dict(coef=float(s2[-1]), sigma=float(e2[-1]), t=float(s2[-1]/e2[-1]),
                                      ZP_amb_quadratic=float(s2[0]),
                                      m_sol_amb_quadratic=float(s2[0] - BV_SOL*s2[2] - BV_SOL**2*s2[3]))
    # (3) Spearman entre residus i B−V
    rho, p = stats.spearmanr(b, r)
    out['spearman_residu_vs_BV'] = dict(rho=float(rho), p=float(p), n=int(ok.sum()))
    # (4) residus contra X i contra V (linealitat), informatius
    out['spearman_residu_vs_dX'] = dict(zip(('rho', 'p'), map(float, stats.spearmanr(dX[ok], r))))
    return out


def permutation_c(y, BV, dX, c_obs, rng):
    """Nul del terme de color: es barreja el (B−V) entre estrelles i es repeteix tot l'ajust (amb retall)."""
    cs = np.empty(NPERM)
    for i in range(NPERM):
        bp = rng.permutation(BV)
        A = np.column_stack([np.ones(len(y)), -dX, -bp])
        s, *_ = wls(A, y)
        cs[i] = s[2]
    p = float((np.sum(np.abs(cs) >= abs(c_obs)) + 1)/(NPERM + 1))
    return dict(n_permutacions=NPERM, llavor=SEED, c_obs=float(c_obs), p_bilateral=p,
                c_perm_p50=float(np.median(cs)), c_perm_p2_5=float(np.percentile(cs, 2.5)),
                c_perm_p97_5=float(np.percentile(cs, 97.5)))


def jackknife(y, BV, dX, Rsun_px):
    n = len(y)
    zs, ms, fs = [], [], []
    for j in range(n):
        keep = np.ones(n, bool)
        keep[j] = False
        A = np.column_stack([np.ones(keep.sum()), -dX[keep], -BV[keep]])
        s, e, ok, rms, cov = wls(A, y[keep])
        zs.append(s[0])
        ms.append(s[0] - BV_SOL*s[2])
    zs, ms = np.array(zs), np.array(ms)
    k = n
    sj = lambda v: float(np.sqrt((k-1)/k*np.sum((v-v.mean())**2)))  # noqa: E731
    return dict(n=k, sigma_ZP=sj(zs), sigma_m_sol=sj(ms), sigma_fac_rel=float(0.4*np.log(10)*sj(ms)),
                m_sol_min=float(ms.min()), m_sol_max=float(ms.max())), ms


def main():
    t0 = time.time()
    entrades = {}
    for nom in ('final_match_r6.csv', 'final_solution.json', 'cat2_r6.csv', 'zp.json', 'zp2.json', 'zp_r6.csv',
                'zp2_r6.csv', 'phot_r6.npz', 'cogf_r6.npz', 'corona2.csv'):
        p = Path(nom)
        if p.exists():
            entrades[rel(p)] = sha256(p)
    tab = pd.read_csv('final_match_r6.csv')
    sol = json.load(open('final_solution.json'))
    S = sol['r6']
    scale = S['scale']                    # la mateixa que corona2.py (lineal)
    Rsun_px = RSUN_AS/scale
    alt, X, Xsun, salt = airmass(tab)
    # comprovació: la massa d'aire ha de ser la mateixa que la de zp_r6.csv de zp.py
    zr = pd.read_csv('zp_r6.csv')
    dXcheck = float(np.nanmax(np.abs(zr.X.values - X)))
    zpj = json.load(open('zp.json'))
    dXsun = abs(zpj['r6']['Xsun'] - Xsun)
    BVall = tab.BV.values.astype(float)
    hipmag = tab.HIP.notna().values
    rng = np.random.default_rng(SEED)

    resultat = dict(
        tasca='msb_calibrat_20261011/zp_canal', data=time.strftime('%Y-%m-%dT%H:%M:%S'),
        model='V - m_c = ZP_c - k_c (X - X_sun) - c_c (B-V); F_sun,c = 10^(0.4 (ZP_c + 26.75 - 0.653 c_c)); '
              'fac_c = pi R_sun,px^2 / F_sun,c',
        unitats=dict(ZP='mag (V - m_inst a X del Sol i B-V = 0), m_inst = -2.5 log10(ADU/s del canal, superficie completa)',
                     fac='B/B_sun per ADU/s i pixel natiu del canal c (dark restat, sense flat, sense balanc de blancs)',
                     F_sol='ADU/s del canal (Sol sencer a traves de la massa d aire X_sun)'),
        constants=dict(BV_sol=BV_SOL, V_sol=M_SOL, R_sol_arcsec=RSUN_AS, escala_arcsec_px=scale,
                       R_sol_px=Rsun_px, X_sol=Xsun, alt_sol_refractada_deg=salt, obertura_px=RAP,
                       normalitzacio_cog_px=RAP_NORM, anell_px=[26, 40], retall_sigma=2.5),
        comprovacions=dict(max_dif_X_vs_zp_r6_csv=dXcheck, dif_Xsun_vs_zp_json=dXsun),
        avisos=[
            "Les sigmes 'sigma_m_sol' i 'sigma_fac_rel' venen de la covariancia del wls amb el conjunt "
            "d'estrelles que queda despres del retall: no inclouen la incertesa de QUINES estrelles queden. "
            "Vegeu SENSIBILITAT_ZP.json (deixar-ne-una-fora i bootstrap, afegits post hoc).",
            "La formula del jackknife ((n-1)/n Σ...) no es valida per a un estimador discontinu com aquest "
            "(retall iteratiu): les sigmes del bloc 'jackknife' estan inflades. Es dona com a senyal de fragilitat; "
            "el que es pot llegir son m_sol_min i m_sol_max.",
            "Canal blau: guany anomal (4,33 e-/ADU), PSF 1,4 vegades mes ampla, senyal molt extingit (X ~ 6), "
            "la meitat de les estrelles retallades i corba de creixement no monotona. No ha de fixar cap conclusio.",
            "k_c no es el coeficient d'extincio: esta barrejat amb el vinyetatge (nota 75 §5.2).",
            "Unitats per pixel natiu del canal, sense flat, sense balanc de blancs ni matriu de color.",
        ],
        canals={}, variants={}, controls_nuls={}, jackknife={})

    per_estrella = tab[['det', 'HIP', 'TYC', 'V', 'BV', 'x', 'y']].copy()
    per_estrella['X'] = X
    per_estrella['dX'] = X - Xsun
    dX = X - Xsun

    for var in ('interp', 'natiu'):
        for ch in 'RGB':
            ph = minst_from_phot(CANAL/f'phot_r6_{ch}_{var}.npz', tab)
            entrades[rel(CANAL/f'phot_r6_{ch}_{var}.npz')] = sha256(CANAL/f'phot_r6_{ch}_{var}.npz')
            fin = np.isfinite(ph['minst'])
            y_all = tab.V.values - ph['minst']
            # zp2.py descarta les estrelles sense fotometria vàlida abans d'ajustar
            y = y_all[fin]
            BV = BVall[fin]
            dXf = dX[fin]
            A = np.column_stack([np.ones(len(y)), -dXf, -BV])
            s, e, ok, rms, cov = wls(A, y)
            fs = sol_factor(s[0], s[2], cov, Rsun_px)
            # sense color i només Hipparcos (com zp2.py / corona2.py)
            A0 = np.column_stack([np.ones(len(y)), -dXf])
            s0, e0, ok0, rms0, cov0 = wls(A0, y)
            fac_nc = float(np.pi*Rsun_px**2/10**(0.4*(s0[0] - M_SOL)))
            hm = hipmag[fin]
            sh, eh, okh, rmsh, covh = wls(A[hm], y[hm])
            fsh = sol_factor(sh[0], sh[2], covh, Rsun_px)
            # el factor «sense color» de corona2.py fa servir el ZP del model amb color i treu el terme
            fac_nocolor_c2 = float(np.pi*Rsun_px**2/10**(0.4*(s[0] - M_SOL)))
            rec = dict(n=int(ok.sum()), n_amb_fotometria=int(fin.sum()), rms=rms,
                       ZP=float(s[0]), eZP=float(e[0]), k=float(s[1]), ek=float(e[1]),
                       c=float(s[2]), ec=float(e[2]),
                       cov_ZP_k_c=cov.tolist(), corr_ZP_c=float(cov[0, 2]/np.sqrt(cov[0, 0]*cov[2, 2])),
                       **fs,
                       fac_nocolor_corona2=fac_nocolor_c2,
                       model_sense_color=dict(ZP=float(s0[0]), eZP=float(e0[0]), k=float(s0[1]), n=int(ok0.sum()),
                                              rms=rms0, fac=fac_nc),
                       nomes_V_Hipparcos=dict(ZP=float(sh[0]), eZP=float(eh[0]), c=float(sh[2]), n=int(okh.sum()),
                                              rms=rmsh, fac=fsh['fac'], sigma_fac_rel=fsh['sigma_fac_rel']),
                       correccio_obertura=ph['apcorr'], plateau_cog=ph['plateau'], cog=ph['cog'],
                       estrelles_usades=tab.det.values[fin][ok].tolist(),
                       estrelles_retallades=tab.det.values[fin][~ok].tolist(),
                       estrelles_sense_fotometria=tab.det.values[~fin].tolist())
            key = f'{ch}_{var}'
            resid = np.full(len(tab), np.nan)
            resid[fin] = y - A@s
            used = np.zeros(len(tab), bool)
            used[np.where(fin)[0][ok]] = True
            per_estrella[f'minst_{key}'] = ph['minst']
            per_estrella[f'resid_{key}'] = resid
            per_estrella[f'usada_{key}'] = used
            per_estrella[f'nfotogrames_{key}'] = ph['nframes']
            if var == 'interp':
                nc = null_controls(y, BV, dXf, ok, s, rng, A)
                nc['permutacio_terme_color'] = permutation_c(y, BV, dXf, s[2], np.random.default_rng(SEED))
                resultat['controls_nuls'][ch] = nc
                jk, _ = jackknife(y, BV, dXf, Rsun_px)
                resultat['jackknife'][ch] = jk
                resultat['canals'][ch] = rec
            else:
                resultat['variants'][f'natiu_{ch}'] = rec
            print(f'{key:9s} n={ok.sum():2d}/{fin.sum():2d} rms={rms:.3f} ZP={s[0]:+.4f}±{e[0]:.4f} '
                  f'k={s[1]:+.3f}±{e[1]:.3f} c={s[2]:+.4f}±{e[2]:.4f}  m☉={fs["m_sol"]:+.4f}±{fs["sigma_m_sol"]:.4f} '
                  f'fac={fs["fac"]:.4e} (±{100*fs["sigma_fac_rel"]:.1f} %)  apcorr={ph["apcorr"]:.4f}')

    # ---------------- CONTROL OBLIGATORI (predeclarat): verd = 17-08 a l'1 %
    G = resultat['canals']['G']
    zp2w = json.load(open('zp2.json'))['r6']
    ctl = dict(
        referencia='Resultats_acceptacio_2026-08-17/zp2.json i corona2.csv (ZP +14,2052 ± 0,040; fac 2,7714e-11)',
        ZP=G['ZP'], eZP=G['eZP'], fac=G['fac'],
        dif_ZP_mag=G['ZP'] - REF_G['ZPsun'], dif_fac_rel=G['fac']/REF_G['fac'] - 1,
        dif_eZP=G['eZP'] - REF_G['eZPsun'], n=G['n'], n_ref=REF_G['n'],
        igual_a_zp2_json_del_WORK=dict(ZP=zp2w['ZPsun'], dif=G['ZP'] - zp2w['ZPsun'], c=zp2w['c'], k=zp2w['k']),
        tolerancia_fac_rel=TOL_FAC)
    ctl['passa'] = bool(abs(ctl['dif_fac_rel']) <= TOL_FAC and abs(G['ZP'] - REF_G['ZPsun']) <= 0.040
                        and G['n'] == REF_G['n'])
    resultat['control_verd'] = ctl
    print(f"\nCONTROL VERD: ZP {G['ZP']:+.5f} (ref {REF_G['ZPsun']:+.5f}, dif {ctl['dif_ZP_mag']:+.2e}); "
          f"fac {G['fac']:.5e} (ref {REF_G['fac']:.5e}, dif {100*ctl['dif_fac_rel']:+.3f} %); n {G['n']} → "
          f"{'PASSA' if ctl['passa'] else 'NO PASSA'}")
    if not ctl['passa']:
        json.dump(resultat, open(CANAL/'ZP_CANAL_CONTROL_FALLIT.json', 'w'), indent=1, ensure_ascii=False)
        print('⛔ El control del verd no passa: m\'aturo i no escric ZP_CANAL.json.')
        sys.exit(3)

    # ---------------- quocients al color del Sol i sensibilitat
    q = {}
    for ch in 'RB':
        C = resultat['canals'][ch]
        # quocient F☉,c/F☉,G; σ: en quadratura (σ independents) i per jackknife conjunt
        r = C['F_sol_ADU_s']/G['F_sol_ADU_s']
        s_ind = 0.4*np.log(10)*np.hypot(C['sigma_m_sol'], G['sigma_m_sol'])
        q[f'F_sol_{ch}_sobre_G'] = dict(valor=float(r), sigma_rel_independent=float(s_ind))
    resultat['quocients_sol'] = q
    # jackknife conjunt (mateixa estrella fora als tres canals) per als quocients
    phs = {ch: minst_from_phot(CANAL/f'phot_r6_{ch}_interp.npz', tab) for ch in 'RGB'}
    finall = np.all([np.isfinite(phs[ch]['minst']) for ch in 'RGB'], axis=0)
    ms_jk = {}
    for ch in 'RGB':
        y = (tab.V.values - phs[ch]['minst'])[finall]
        _, ms_jk[ch] = jackknife(y, BVall[finall], dX[finall], Rsun_px)
    nj = finall.sum()
    for ch in 'RB':
        d = ms_jk[ch] - ms_jk['G']
        sj = float(np.sqrt((nj-1)/nj*np.sum((d-d.mean())**2)))
        q[f'F_sol_{ch}_sobre_G']['sigma_rel_jackknife_conjunt'] = float(0.4*np.log(10)*sj)
    # conjunt d'estrelles del verd imposat a R i B (sense retall)
    usG = set(G['estrelles_usades'])
    comu_set = {}
    for ch in 'RGB':
        ph = phs[ch]
        fin = np.isfinite(ph['minst'])
        okc = np.array([d in usG for d in tab.det.values]) & fin
        y = tab.V.values - ph['minst']
        A = np.column_stack([np.ones(len(y)), -dX, -BVall])
        yy = np.where(fin, y, 0.0)
        s, cov, rms = fit_fixed(A, yy, okc)
        fs = sol_factor(s[0], s[2], cov, Rsun_px)
        comu_set[ch] = dict(n=int(okc.sum()), ZP=float(s[0]), k=float(s[1]), c=float(s[2]), rms=rms,
                            fac=fs['fac'], sigma_fac_rel=fs['sigma_fac_rel'], F_sol_ADU_s=fs['F_sol_ADU_s'])
    for ch in 'RB':
        comu_set[f'F_sol_{ch}_sobre_G'] = comu_set[ch]['F_sol_ADU_s']/comu_set['G']['F_sol_ADU_s']
    resultat['variants']['conjunt_estrelles_del_verd'] = comu_set

    per_estrella.to_csv(CANAL/'zp_canal_per_estrella.csv', index=False)
    entrades_tasca = {rel(CANAL/'zp_canal_per_estrella.csv'): sha256(CANAL/'zp_canal_per_estrella.csv')}
    RES.mkdir(parents=True, exist_ok=True)
    resultat['fitxers'] = dict(per_estrella=rel(CANAL/'zp_canal_per_estrella.csv'),
                               rebut=rel(RES/'ZP_CANAL_rebut.json'))
    json.dump(resultat, open(RES/'ZP_CANAL.json', 'w'), indent=1, ensure_ascii=False)
    rebut = dict(tasca='msb_calibrat_20261011/zp_canal', guio=rel(Path(__file__)),
                 sha256_guio=sha256(Path(__file__)), data=resultat['data'],
                 entrades=entrades, sortides={rel(RES/'ZP_CANAL.json'): sha256(RES/'ZP_CANAL.json'),
                                               **entrades_tasca},
                 segons=round(time.time()-t0, 1))
    json.dump(rebut, open(RES/'ZP_CANAL_rebut.json', 'w'), indent=1, ensure_ascii=False)
    print(f'\nEscrit {rel(RES/"ZP_CANAL.json")} ({time.time()-t0:.1f} s)')


if __name__ == '__main__':
    main()

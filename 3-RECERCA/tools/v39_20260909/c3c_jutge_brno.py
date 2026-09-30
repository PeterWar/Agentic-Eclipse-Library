"""C3c (V39) · JUTGE EXTERN INDEPENDENT: les fotos finals de Brno (Druckmüller), només jutge, mai font (norma del projecte). Motiu: el «jutge extern»
de c3 (Vixen original a quatre finestres «on la base és Sony») NO és independent des de la V34: el pes de la Vixen a la fusió hi val 0,37–0,44
(corr(original, Vixen V38) = 1,000), o sigui que la base conté el jutge; i no existeix cap finestra de 768 px amb pes Vixen < 0,03 (mediana 0,34–0,47
a tot el camp). Brno és un altre instrument i un altre processat: independent de debò.
Mètode congelat de research/tools/v30/compare_brno.py: anells polars 1,2–9,0 R☉ (pas 0,2, 1440 azimuts), geometria del llenç (angle de
geometria_v27) i registre de cada foto Brno (auditoria_estructura/registre2.json), suavitzat angular gaussià (1° i 4,5°) normalitzat pel suport,
estructura per anell (x − mediana)/MAD, Pearson per anell contra cada Brno, mitjana de les quatre, control nul (gir de 180°), control Brno×Brno.
Afegit V39: TRANSFERÈNCIA de l'estructura confirmada per Brno: cov(anell(V39) − mediana, estructura Brno) / cov(anell(V38) − mediana, estructura Brno)
per anell (mateixa referència als dos: 1 = la capa V39 conserva tota la component que Brno confirma; < 1 = la perd en aquesta proporció),
i el quocient de rms per anell V39/V38. Capes: les lliurades (u16, com les veu Pere). Només lectura."""
from comu39 import *
import warnings
from scipy.ndimage import gaussian_filter1d
AUD = ROOT / 'research/tools/auditoria_estructura'
sys.path.insert(0, str(AUD)); import nucli as N
REG = json.loads((AUD / 'registre2.json').read_text()); GEO = ROOT / 'research/tools/v25_lineal/cau_v25/geometria_v27.json'
M = np.asarray(json.loads(GEO.read_text())['M_llenc_a_v23']); ANGLE = float(np.arctan2(M[1, 0], M[0, 0]))
RAD = np.round(np.arange(1.2, 9.01, .2), 2); NTH = 1440; RANGES = [(1.2, 3), (3, 5), (5, 9.01)]
BRNO = ['TSE_2026_200mm_DHS.png', 'TSE_2026_400mm_DHS.png', 'TSE_2026_530mm_DHS.png', 'TSE2026_Trigaza_800mm.png']
PC38 = ROOT / 'research/tools/v38_20260908/purs/cau'; PC39 = HERE39 / 'purs/cau'
LAYERS = {'01': (CAU38 / '01_v38_u16.npy', CAU39 / '01_v39_u16.npy'), '04': (CAU38 / '04_v38_u16.npy', CAU39 / '04_v39_u16.npy'), '05': (CAU38 / '05_v38_u16.npy', CAU39 / '05_v39_u16.npy'), '06': (CAU38 / '06_v38_u16.npy', CAU39 / '06_v39_u16.npy'),
          'P03': (PC38 / 'P03_MGN_u16.npy', PC39 / 'P03_MGN_u16.npy'), 'P04': (PC38 / 'P04_WOW_u16.npy', PC39 / 'P04_WOW_u16.npy'), 'P05': (PC38 / 'P05_WOW_bilateral_u16.npy', PC39 / 'P05_WOW_bilateral_u16.npy')}


def suau(p, deg):
    m = np.isfinite(p); s = deg / 360 * NTH; num = gaussian_filter1d(np.where(m, p, 0), s, axis=1, mode='wrap'); den = gaussian_filter1d(m.astype(float), s, axis=1, mode='wrap')
    return np.where(m, num / np.maximum(den, 1e-12), np.nan)


def estr(p, deg):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning); return N.estructura(suau(p, deg))


def desviacio(p, deg):
    """Anell suavitzat menys la seva mediana, SENSE dividir per la MAD (per a la transferència: cal conservar l'amplitud)."""
    q = suau(p, deg)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning); return q - np.nanmedian(q, axis=1, keepdims=True)


def avg(a):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning); return np.nanmean(a, axis=0)


def resum(a):
    return [float(np.nanmedian(a[(RAD >= lo) & (RAD < hi)])) for lo, hi in RANGES]


def covs(d38, d39, eb):
    """Per anell: (Σ d38·eb, Σ d39·eb, Σ d38², Σ eb², n) sobre els azimuts finits als tres; sense normalitzar (per agregar entre Brno i anells)."""
    out = np.zeros((len(RAD), 5))
    for i in range(len(RAD)):
        k = np.isfinite(d38[i]) & np.isfinite(d39[i]) & np.isfinite(eb[i])
        if k.sum() < 64: continue
        b = eb[i][k] - eb[i][k].mean(); a38 = d38[i][k] - d38[i][k].mean(); a39 = d39[i][k] - d39[i][k].mean()
        out[i] = [(a38 * b).sum(), (a39 * b).sum(), (a38 * a38).sum(), (b * b).sum(), k.sum()]
    return out


def transferencia(cv_list, sel=None, minim_corr=0.10):
    """Quocient de covariàncies AGREGADES Σ_b Σ_θ (d39·eb) / Σ_b Σ_θ (d38·eb) sobre els anells de `sel` (o cadascun): els anells on la correlació
    agregada V38×Brno és feble (< 0,10) no entren (denominador sense significat). Retorna (quocient, correlació agregada V38) o (nan, corr)."""
    C = np.sum(cv_list, axis=0)   # (anells, 5) sumat sobre els Brno
    if sel is None:
        out = np.full(len(RAD), np.nan); cr = np.full(len(RAD), np.nan)
        for i in range(len(RAD)):
            den = np.sqrt(C[i, 2] * C[i, 3]); cr[i] = C[i, 0] / den if den > 0 else np.nan
            if den > 0 and abs(cr[i]) >= minim_corr: out[i] = C[i, 1] / C[i, 0]
        return out, cr
    rows = C[sel]; den = np.sqrt(rows[:, 2].sum() * rows[:, 3].sum()); cr = rows[:, 0].sum() / den if den > 0 else np.nan
    return (rows[:, 1].sum() / rows[:, 0].sum() if den > 0 and abs(cr) >= minim_corr and rows[:, 0].sum() != 0 else np.nan), cr


def main():
    B = {}
    for name in BRNO:
        im, *_ = N.carrega_brno(name); rg = REG[name]; B[name] = N.mostreja(im, rg['cy'], rg['cx'], rg['R_sol_px'], RAD, NTH, ang0=np.deg2rad(rg['gir_deg'])); del im
    rep = {'metode': 'compare_brno v30 congelat (anells 1,2–9 R☉ pas 0,2, 1440 az, estructura (x−med)/MAD, Pearson per anell, mitjana de 4 Brno, nul 180°) + transferència = quocient de covariàncies AGREGADES (sumes sobre les 4 Brno, els anells del rang i els azimuts) cov(V39,Brno)/cov(V38,Brno), només on la correlació agregada V38×Brno ≥ 0,10; un-Brno-fora (mín/màx) i 8 sectors azimutals (p16/mediana/p84); rms V39/V38 per anell; a 1° i 4,5°', 'angle_deg': float(np.degrees(ANGLE)), 'rangs': RANGES, 'capes': {}}
    for deg in (1.0, 4.5):
        eb = {k: estr(p, deg) for k, p in B.items()}
        ctrl = avg(np.stack([N.corr_per_anell(eb[a], eb[b]) for j, a in enumerate(BRNO) for b in BRNO[j + 1:]])); rep[f'BrnoBrno_{deg:g}deg'] = {'r': resum(ctrl), 'per_anell': ctrl.tolist()}
        log(f'{deg:g}°: control Brno×Brno per rangs {RANGES}: ' + ' '.join(f'{v:+.3f}' for v in resum(ctrl)))
    for k, (p38, p39) in LAYERS.items():
        pol = {}
        for lab, p in (('V38', p38), ('V39', p39)):
            a = np.load(p, mmap_mode='r'); assert a.shape == (H, W) and a.dtype == np.uint16
            pol[lab] = N.mostreja(a, CY, CX, RS, RAD, NTH, ang0=ANGLE).astype(np.float64) / 65535.0 - 0.5; del a
        row = {}
        for deg in (1.0, 4.5):
            eb = {kk: estr(p, deg) for kk, p in B.items()}; e38 = estr(pol['V38'], deg); e39 = estr(pol['V39'], deg); d38 = desviacio(pol['V38'], deg); d39 = desviacio(pol['V39'], deg)
            c38 = avg(np.stack([N.corr_per_anell(e38, eb[b]) for b in BRNO])); c39 = avg(np.stack([N.corr_per_anell(e39, eb[b]) for b in BRNO]))
            n39 = avg(np.stack([N.corr_per_anell(np.roll(e39, NTH // 2, axis=1), eb[b]) for b in BRNO]))
            cvl = [covs(d38, d39, eb[b]) for b in BRNO]; tr_anell, cr_anell = transferencia(cvl)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning); rms = np.nanstd(d39, axis=1) / np.maximum(np.nanstd(d38, axis=1), 1e-12)
            # per rang: quocient AGREGAT (sumes sobre Brno, anells i azimuts), un-Brno-fora (mín/màx) i sectors azimutals (8 sectors de 45°: p16–p84)
            tr_rang = []; loo = []; sect = []
            for lo, hi in RANGES:
                sel = (RAD >= lo) & (RAD < hi); t, cr = transferencia(cvl, sel); tr_rang.append(t)
                l1 = [transferencia([c for j, c in enumerate(cvl) if j != jj], sel)[0] for jj in range(len(BRNO))]; l1 = [v for v in l1 if np.isfinite(v)]; loo.append([min(l1), max(l1)] if l1 else [np.nan, np.nan])
                ss = []
                for q in range(8):
                    az = slice(q * NTH // 8, (q + 1) * NTH // 8); cvq = [covs(d38[:, az], d39[:, az], eb[b][:, az]) for b in BRNO]; ss.append(transferencia(cvq, sel, minim_corr=0.05)[0])
                ss = [v for v in ss if np.isfinite(v)]; sect.append([float(np.percentile(ss, 16)), float(np.median(ss)), float(np.percentile(ss, 84)), len(ss)] if ss else [np.nan] * 4)
            row[f'{deg:g}deg'] = {'corr_V38': resum(c38), 'corr_V39': resum(c39), 'nul_V39': resum(n39), 'transferencia_cov': [float(v) for v in tr_rang], 'transferencia_un_brno_fora_min_max': loo, 'transferencia_sectors_p16_med_p84_n': sect, 'transferencia_mediana_anells': resum(tr_anell), 'rms_V39_V38': resum(rms),
                                  'per_anell': {'corr_V38': c38.tolist(), 'corr_V39': c39.tolist(), 'nul': n39.tolist(), 'transferencia': tr_anell.tolist(), 'corr_agregada_V38': cr_anell.tolist(), 'rms': rms.tolist()}}
            log(f'{k} {deg:g}°: corr Brno V38 ' + ' '.join(f'{v:+.3f}' for v in resum(c38)) + ' → V39 ' + ' '.join(f'{v:+.3f}' for v in resum(c39)) + ' (nul ' + ' '.join(f'{v:+.3f}' for v in resum(n39)) + ') · transferència agregada ' + ' '.join(f'{v:.3f}' for v in tr_rang) + ' · un-Brno-fora ' + ' '.join(f'[{a:.2f},{b:.2f}]' for a, b in loo) + ' · sectors p16/med/p84 ' + ' '.join(f'{a:.2f}/{b:.2f}/{c:.2f}' for a, b, c, _ in sect) + ' · rms ×' + ' '.join(f'{v:.2f}' for v in resum(rms)))
        rep['capes'][k] = row
    (REB39 / 'C3c_jutge_brno.json').write_text(json.dumps(rep, indent=1)); log('C3c fet')


if __name__ == '__main__':
    main()

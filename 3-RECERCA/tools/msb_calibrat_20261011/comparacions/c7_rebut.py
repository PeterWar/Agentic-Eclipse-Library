"""c7 · Rebut de les comparacions (SHA-256 de totes les entrades, del codi i de les sortides) i una prova de sensibilitat del K-Cor.
Encàrrec «comparacions», 11-10-2026.

Sensibilitat (HIPOTÈTICA, NO APLICADA a cap resultat): el pB L2 del K-Cor d'aquell dia és negatiu més enllà d'1,95 R☉ (residu de la
resta de la polarització del cel). Si el mateix desplaçament additiu que es mesura a 2,6–2,9 R☉ hi fos també als anells interiors,
el model pB/p + F pujaria en (−desplaçament)/p. Es dona per veure'n l'ordre de magnitud; la forma radial real del residu no es coneix.
Escriu comparacions/RECEIPT_comparacions.json."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmp_comu as cc   # noqa: E402

mc = cc.mc
T0 = time.time()
SCR = Path(sys.argv[1]) if len(sys.argv) > 1 else None          # carpeta (fora del projecte) amb els PDF dels models de F, si n'hi ha

# ---------------------------------------------------------------- sensibilitat al residu del cel del K-Cor
ref = np.mean([cc.carrega_kcor(s)[0] for s in cc.KCOR_TOT], axis=0)
g = cc.carrega_kcor(cc.KCOR_TOT[0])[1]
yy, xx = np.mgrid[0:1024, 0:1024].astype(np.float64)
r, pa = g.polar(xx, yy)
perfil = {}
for a in np.arange(1.15, 3.0, 0.1):
    m = (r >= a) & (r < a + 0.1)
    perfil[f'{a:.2f}-{a + 0.1:.2f}'] = dict(mediana=float(np.median(ref[m])), p10=float(np.percentile(ref[m], 10)),
                                             p90=float(np.percentile(ref[m], 90)), fraccio_negativa=float((ref[m] < 0).mean()))
m = (r >= 2.6) & (r < 2.9)
desp = float(np.median(ref[m]))
K = np.load(cc.RES / 'kcor/kcor_caselles.npz')
N = np.load(cc.RES / 'caselles_nostra.npz')
kj = json.load(open(cc.RES / 'kcor/KCOR.json'))
sens = []
for i, a in enumerate([tuple(x) for x in K['anells']][:3]):
    p = kj['p_mediana_per_anell']['Baumbach-Allen'][i]
    mod = K['model_Baumbach-Allen_vdH1950'][i]
    y = np.where(K['usable'][i], N['kcor_msb'][i], np.nan)
    q0 = cc.quocients(y, mod)['quocient_medianes']
    q1 = cc.quocients(y, mod - desp / p)['quocient_medianes']
    sens.append(dict(anell=list(a), p=p, quocient_adoptat=q0, quocient_si_el_residu_fos_constant=q1, canvi=q1 / q0 - 1))
print('desplaçament del pB del K-Cor a 2,6–2,9 R☉:', desp, '\n', json.dumps(sens, indent=0))

# ---------------------------------------------------------------- rebut
entr = {}
for p in [cc.PLE / 'msb_ple.npy', cc.PLE / 'msb_noext_ple.npy', cc.PLE / 'flags_ple.npy', mc.MAPA / 'msb_mapa_2x2.fits',
          mc.MAPA / 'CEL.json', mc.MAPA / 'ZONES.json', mc.MAPA / 'massa_aire_graella.npz', mc.MAPA / 'zona_lunar_gap.npz',
          mc.MAPA / 'perfils/perfil_azimutal.csv', mc.MAPA / 'perfils/perfil_sectors_10graus.csv', mc.MAPA / 'RECEIPT_mapa.json',
          mc.RES / 'zp_canal/ZP_CANAL.json', mc.RES / 'zp_canal/SENSIBILITAT_ZP.json',
          cc.D11 / 'lasco_calib/c2_expfactor_260812.dat', cc.D01 / 'lasco_calib/c2vig_final.fts',
          cc.D01 / 'kcor' / cc.GIF_C9, cc.RES01 / 'brillantor/C9_BRILLANTOR.json', cc.RES01 / 'GEOMETRIA_FINAL.json',
          cc.TOOLS01 / 'comu_comp.py', cc.TOOLS01 / 'c9_brillantor.py', mc.EINES / 'msb_comu.py']:
    entr[cc.rel(p)] = cc.sha256(p)
for f in cc.C2_FITXERS:
    entr[cc.rel(cc.D01 / 'soho_lasco' / f)] = cc.sha256(cc.D01 / 'soho_lasco' / f)
for s in cc.KCOR_TOT + cc.KCOR_CTRL:
    p = cc.D11 / 'kcor' / f'{s}_kcor_l2_pb.fts.gz'; entr[cc.rel(p)] = cc.sha256(p)
for s in cc.KCOR_AVG:
    p = cc.D11 / 'kcor' / f'{s}_kcor_l2_pb_avg.fts.gz'; entr[cc.rel(p)] = cc.sha256(p)
p = cc.D11 / 'kcor/20260812.kcor.radial.intensity.txt'; entr[cc.rel(p)] = cc.sha256(p)
entr['fusion_total_v42.npy, support_v42.npy, weight_vixen_v42.npy (Paperera de Pere, només lectura)'] = {
    k: mc.SHA_CAU[k] for k in ('fusion_total_v42.npy', 'support_v42.npy', 'weight_vixen_v42.npy')}
fonts_fora = dict(
    KL1985=dict(url='https://www.cambridge.org/core/services/aop-cambridge-core/content/view/430F969D2B9FBA0BAC746FE9E654933A/'
                    'S0252921100084359a.pdf', sha256=json.load(open(cc.RES / 'models_f/F_KL1985_digitalitzat.json'))['pdf_sha256'],
                doi='10.1017/S0252921100084359'),
    vdH1950=dict(url='https://articles.adsabs.harvard.edu/pdf/1950BAN....11..135V', bibcode='1950BAN....11..135V',
                 sha256='b47b8c477f4ccdf0f01fb62d368f139ad657799bb34f26c37808ff46b3d5bc96'),
    Saito1977=dict(url='https://articles.adsabs.harvard.edu/pdf/1977SoPh...55..121S', doi='10.1007/BF00150879',
                   sha256='be418f231a1b4b987b0811284e8041cdea4d32fde9d00efd3c546db457bc126d'),
    Colaninno_Howard_2015_eq8=dict(url='https://pmc.ncbi.nlm.nih.gov/articles/instance/4479163/bin/11207_2014_635_Article_Equ8.gif',
                                   doi='10.1007/s11207-014-0635-2',
                                   sha256='883d456396039d458f918812a94eb164fc9b6d87d767f7a712cb53a567a4aeff',
                                   lectura='PCF = (3,9 [±0,5]×10^-5 MJD + 5,2 [±0,3])×10^-12; comprovada refent l\'ajust ponderat de la Taula 2 (3,927e-5; 5,202)'),
    nota='Articles llegits per verificar fórmules i taules; NO s\'han copiat al projecte (són a la carpeta de treball de la sessió).')
codi = {cc.rel(p): cc.sha256(p) for p in sorted(cc.AQUI.glob('*.py')) + sorted(cc.AQUI.glob('*.sh'))}
sort = {}
for p in sorted(cc.RES.rglob('*')) + sorted(cc.COMPARTIR.rglob('*')):
    if p.is_file() and p.name != 'RECEIPT_comparacions.json':
        sort[cc.rel(p)] = cc.sha256(p)
json.dump(dict(tasca='msb_calibrat_20261011/comparacions', data=time.strftime('%Y-%m-%dT%H:%M:%S'),
               estat='PROVISIONAL: res enviat ni publicat; cal el sí de Pere',
               entrades_sha256=entr, fonts_externes_llegides=fonts_fora, codi_sha256=codi, sortides_sha256=sort,
               kcor_residu_cel=dict(perfil_mitjana_7=perfil, desplacament_2p6_2p9=desp, sensibilitat_hipotetica_no_aplicada=sens),
               python=sys.version.split()[0], segons=round(time.time() - T0, 1)),
          open(cc.RES / 'RECEIPT_comparacions.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(f'rebut: {len(entr)} entrades, {len(codi)} fitxers de codi, {len(sort)} sortides ({time.time() - T0:.0f} s)')

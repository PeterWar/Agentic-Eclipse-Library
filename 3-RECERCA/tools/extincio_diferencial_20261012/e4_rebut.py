"""e4 · Rebut de la comparació «extinció diferencial» (12-10-2026): SHA-256 de les entrades, del codi i de les sortides,
les xifres principals i les proves (de E1_MASSA_AIRE_FINAL.json, E2_PIS1.json i E3_PIS2.json).
Escriu Sortides/extincio_diferencial_20261012/REBUT_extincio_diferencial.json. No toca cap entrada."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ed_comu as ed            # noqa: E402

mc = ed.mc
T0 = time.time()
cau = mc.troba_cau()
entrades = {
    'compost_lineal fusion_total_v42.npy': cau / 'fusion_total_v42.npy',
    'suport support_v42.npy': cau / 'support_v42.npy',
    'final V125-FINAL.psb': ed.PSB,
    'cel per canal (v2) CEL_CANALS_v2.json': ed.CEL_CANALS,
    'geometria de la final GEOMETRIA_FINAL.json': ed.GEOF,
    'nord i est de la placa mars_final.json': mc._MARS,
    'escala de la placa estrelles_final.json': mc._ESTR,
    'massa d\'aire del llenç V42 massa_aire_graella.npz': ed.GRAELLA_V42,
    'matriu de color 572A2955.CR3 (capçalera, rawpy)': mc.CR3_MATRIU,
}
sha_e = {}
for nom, p in entrades.items():
    sha_e[nom] = dict(ruta=ed.rel(p), sha256=ed.sha256(p), bytes=Path(p).stat().st_size)
    print(nom, sha_e[nom]['sha256'][:16], flush=True)
esperat = {'compost_lineal fusion_total_v42.npy': mc.SHA_CAU['fusion_total_v42.npy'],
           'suport support_v42.npy': mc.SHA_CAU['support_v42.npy'], 'final V125-FINAL.psb': ed.SHA_PSB_ESTAT}
comprovacio = {k: sha_e[k]['sha256'] == v for k, v in esperat.items()}

codi = {p.name: ed.sha256(p) for p in sorted(ed.EINES.glob('*.py')) + sorted(ed.EINES.glob('*.sh'))}
sortides = {}
for p in sorted(list(ed.SORT.glob('*.jpg')) + list(ed.SORT.glob('*.md')) + list(ed.RES.glob('*.json')) + list(ed.RES.glob('*.npz'))):
    sortides[ed.rel(p)] = dict(sha256=ed.sha256(p), bytes=p.stat().st_size)

E1 = json.load(open(ed.RES / 'E1_MASSA_AIRE_FINAL.json'))
E2 = json.load(open(ed.RES / 'E2_PIS1.json'))
E3 = json.load(open(ed.RES / 'E3_PIS2.json'))
xif = {}
for f in E1['eix_zenit']:
    xif[f"{f['r_Rsol']:g} R☉"] = dict(
        X_zenit=round(f['zenit']['X'], 3), X_horitzo=round(f['horitzo']['X'], 3),
        E_zenit=round(f['zenit']['E'], 3), E_horitzo=round(f['horitzo']['E'], 3),
        llum_rebuda_zenit_pc=round(f['zenit']['llum_rebuda_respecte_del_Sol_pc'], 1),
        llum_rebuda_horitzo_pc=round(f['horitzo']['llum_rebuda_respecte_del_Sol_pc'], 1))

rebut = dict(
    que='Costat a costat perquè Pere decideixi si la imatge publicada s\'ha de corregir de l\'extinció diferencial',
    data=time.strftime('%Y-%m-%dT%H:%M:%S'), autor='Claude',
    photoshop='No s\'ha obert. La V125-FINAL.psb s\'ha llegit amb psd-tools (secció de la imatge fusionada), sense escriure-hi res.',
    imatge_publicada=('La imatge fusionada de la V125-FINAL.psb és la final vigent (ESTAT.md). La V127 i la V125-FINAL_comparacio_v3 '
                      'en porten una d\'idèntica (els seus rebuts). Els JPEG enviats a l\'APOD i pujats a Flickr el 30-09 surten de la V123, '
                      'del mateix marc; la V125 hi afegeix els retocs de Pere (0,2 % dels píxels).'),
    entrades=sha_e, entrades_iguals_a_les_esperades=comprovacio,
    recepta=dict(k_mag_per_massa_aire=ed.K, font_k='nota 78 (0,402 ± 0,036)', E='10^(0,4·k·(X − X☉))',
                 X_sol=E1['X_sol'], h_sol_deg=E1['h_sol_deg'], instant=mc.DATE_OBS,
                 pis1=E2['recepta'], pis2=E3['recepta']),
    xifres_eix_del_zenit=xif, zenit=E1['zenit'],
    proves=dict(massa_aire=dict(contra_llenc_V42=E1['prova_a_contra_llenc_V42'], spline=E1['prova_spline'],
                                E_centre_sol=E1['E_centre_sol']),
                pis1=E2['proves'], pis2=E3['proves'], pis2_fons=E3['fons_r_mes_6_quocient']),
    canvi_visible_pis2=E3['canvi_visible_sectors_15graus'],
    balanc_per_canal=dict(pis1=E2['balanc_per_canal'], pis2=E3['balanc_per_canal']),
    codi=dict(carpeta=ed.rel(ed.EINES), sha256=codi), sortides=sortides,
    no_fet=['Cap correcció cromàtica (la part més vermella cap a l\'horitzó): els coeficients per canal són incerts i el color és decisió de Pere.',
            'Cap PSB nou ni cap canvi a cap fitxer de Pere.', 'Res publicat ni enviat.'],
    segons=round(time.time() - T0, 1))
ed.json_dump(rebut, ed.SORT / 'REBUT_extincio_diferencial.json')
print('iguals a les esperades:', comprovacio)
print(f'fet ({time.time() - T0:.0f} s)')

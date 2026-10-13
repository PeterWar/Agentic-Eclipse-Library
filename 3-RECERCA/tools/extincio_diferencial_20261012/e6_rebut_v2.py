"""e6 · Rebut v2 de la comparació «extinció diferencial» (12-10-2026): el que ha canviat després del verificador.

Comprova i apunta:
  - les entrades (SHA-256 de nou: compost, suport, V125-FINAL.psb i la resta), iguals a les esperades;
  - que totes les sortides del v1 (vistes, JSON, graella, LLEGEIX-ME.md) són byte a byte les que diu el rebut v1 ORIGINAL;
  - que l'únic canvi de codi d'e2 és el docstring (c = 10 → 5 ADU/s): es refà el text vell i se'n comprova el SHA original;
  - els SHA del codi actual, del LLEGEIX-ME_v2.md i d'E5_MESURES_LLEGEIXME_v2.json.
Escriu Sortides/extincio_diferencial_20261012/REBUT_extincio_diferencial_v2.json. No toca cap entrada ni cap sortida del v1."""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ed_comu as ed            # noqa: E402

mc = ed.mc
T0 = time.time()
REBUT_V1 = ed.SORT / 'REBUT_extincio_diferencial.json'
SHA_REBUT_V1_ORIGINAL = '51b3514643cdb55cd9cd2e9a930072bfc66bad9761c1af4236a8433e6858dc9e'   # el de les 13:00:06
SHA_E2_V1 = '1db04c2785de4ac2e778e8c7d359e9b5b62495709c2661069797132e5dbe550f'
DOC_NOU, DOC_VELL = 'c = 5 ADU/s (C_SUAU); gris', 'c = 10 ADU/s; gris'

sha_rebut1 = ed.sha256(REBUT_V1)
rebut1 = json.load(open(REBUT_V1))
rebut1_original = sha_rebut1 == SHA_REBUT_V1_ORIGINAL
print('rebut v1 original:', rebut1_original, flush=True)

# 1. entrades, de nou
entrades = {}
for nom, d in rebut1['entrades'].items():
    p = ed.ARREL / d['ruta']
    s = ed.sha256(p)
    entrades[nom] = dict(ruta=d['ruta'], sha256=s, igual_que_al_v1=s == d['sha256'])
    print(nom, s[:16], 'igual' if s == d['sha256'] else 'DIFERENT', flush=True)
esperat = {'compost_lineal fusion_total_v42.npy': mc.SHA_CAU['fusion_total_v42.npy'],
           'suport support_v42.npy': mc.SHA_CAU['support_v42.npy'], 'final V125-FINAL.psb': ed.SHA_PSB_ESTAT}
iguals_esperades = {k: entrades[k]['sha256'] == v for k, v in esperat.items()}

# 2. sortides del v1: byte a byte iguals (només si el rebut v1 és l'original; si s'ha refet amb executa.sh, es diu)
sortides_v1 = {}
for rel, d in rebut1['sortides'].items():
    s = ed.sha256(ed.ARREL / rel)
    sortides_v1[rel] = dict(sha256=s, igual_que_al_v1=s == d['sha256'])
totes_iguals = all(v['igual_que_al_v1'] for v in sortides_v1.values())
print('sortides del v1 iguals:', totes_iguals, flush=True)

# 3. e2: l'únic canvi és el docstring
p2 = ed.EINES / 'e2_pis1_compost_lineal.py'
txt = p2.read_text()
vell = txt.replace(DOC_NOU, DOC_VELL, 1)
e2_nomes_docstring = (txt.count(DOC_NOU) == 1 and hashlib.sha256(vell.encode()).hexdigest() == SHA_E2_V1)
print('e2: només el docstring', e2_nomes_docstring, flush=True)

codi = {p.name: ed.sha256(p) for p in sorted(ed.EINES.glob('*.py')) + sorted(ed.EINES.glob('*.sh'))}
codi_v1 = rebut1['codi']['sha256']
codi_canvis = {k: ('nou' if k not in codi_v1 else ('igual' if codi_v1[k] == v else 'canviat')) for k, v in codi.items()}

noves = {}
for p in (ed.SORT / 'LLEGEIX-ME_v2.md', ed.RES / 'E5_MESURES_LLEGEIXME_v2.json'):
    noves[ed.rel(p)] = dict(sha256=ed.sha256(p), bytes=p.stat().st_size)
E5 = json.load(open(ed.RES / 'E5_MESURES_LLEGEIXME_v2.json'))

rebut = dict(
    que='Rebut v2 del costat a costat de l\'extinció diferencial: correccions del LLEGEIX-ME després del verificador',
    data=time.strftime('%Y-%m-%dT%H:%M:%S'), autor='Claude',
    substitueix=dict(llegeix_me='Sortides/extincio_diferencial_20261012/LLEGEIX-ME.md (es conserva)',
                     rebut_v1=dict(ruta=ed.rel(REBUT_V1), sha256=sha_rebut1, es_l_original=rebut1_original)),
    photoshop='No s\'ha obert. De la V125-FINAL.psb només s\'han llegit els registres de capa (capes_psb.py) i el SHA.',
    entrades=entrades, entrades_iguals_a_les_esperades=iguals_esperades,
    sortides_v1=dict(totes_iguals=totes_iguals, fitxers=sortides_v1,
                     nota='Cap imatge ni cap JSON del v1 no s\'ha refet ni sobreescrit.'),
    sortides_noves=noves,
    codi=dict(carpeta=ed.rel(ed.EINES), sha256=codi, respecte_del_v1=codi_canvis,
              e2_nomes_docstring=dict(passa=e2_nomes_docstring, canvi=f'«{DOC_VELL}» → «{DOC_NOU}»',
                                      prova='es refà el text vell i el seu SHA-256 és el del rebut v1')),
    correccions=[
        dict(punt='LLEGEIX-ME, pis 2, «El to no canvia»',
             fet='Encapçalament «El to de la corona no canvia; el de la barreja amb el cel, sí, una mica». Taula de R/G i B/G '
                 'codificats per meitats (1,1–4 R☉). Explicació: cap a l\'horitzó el B/G de la corona sobre el cel estimat és 0,06, ≈ 0 '
                 'o negatiu, i el guany no hi afegeix blau.',
             font='E5_MESURES_LLEGEIXME_v2.json pis2_color_per_meitats (d\'E3 balanc_per_canal)'),
        dict(punt='LLEGEIX-ME, pis 2, residu del cel',
             fet='Declarat: −5,4 % al centre de baix (4,9–5,8 R☉), −2,0 % al de dalt, +4,5 % a 4–5 R☉ (corona i error junts). '
                 'Les xifres de cap a l\'horitzó a partir de 3 R☉ en depenen; el −0,1 % a 4 R☉ (E 1,29, fracció −0,004) és un símptoma. '
                 '«Segons el cel estimat» afegit.',
             font='E5_MESURES_LLEGEIXME_v2.json pis2_residu_cel_G i pis2_sector_horitzo_3_i_4_Rsol'),
        dict(punt='LLEGEIX-ME, pis 1, «A la B, s\'iguala»',
             fet='Substituït per la taula de diferències de gris zenit − horitzó, A → B: 43 → 29, 37 → 13, 38 → 4 i 39 → −4 DN '
                 '(1,2–2 / 2–3 / 3–4 / 4–5 R☉). La del verificador (43 → 29, 37 → 11, 38 → 3) també hi és.',
             font='E5_MESURES_LLEGEIXME_v2.json pis1_vistes'),
        dict(punt='xifres petites',
             fet='×1,26 (no ×1,25); el vector EXTINCIO de comu.py només el fa servir f4.py en la capa opcional «07 SOBRE L\'ATMOSFERA», '
                 'que la V125-FINAL no porta; referència 6,024 del mapa v2 (1,1 % global); el subtítol de P2_B («cel intacte») vol dir '
                 'el nivell; docstring d\'e2 (c = 5).',
             font='E5_MESURES_LLEGEIXME_v2.json banda_k_4Rsol_horitzo, factor_global_Xsol_contra_ZPXSUN, capes_V125_FINAL'),
    ],
    mesures_v2=dict(pis1=E5['pis1_vistes']['anells'], pis2_color=E5['pis2_color_per_meitats'], pis2_residu=E5['pis2_residu_cel_G'],
                    banda_k=E5['banda_k_4Rsol_horitzo'], ZPXSUN=E5['factor_global_Xsol_contra_ZPXSUN'], capes=E5['capes_V125_FINAL']),
    no_fet=['Les vistes P2_B i P2_costat_a_costat no s\'han refet: el subtítol de P2_B («el cel … intactes») es matisa al LLEGEIX-ME_v2.',
            'Cap correcció cromàtica. Cap PSB nou. Res publicat ni enviat.'],
    segons=round(time.time() - T0, 1))
ed.json_dump(rebut, ed.SORT / 'REBUT_extincio_diferencial_v2.json')
print('entrades iguals a les esperades:', iguals_esperades)
print('codi respecte del v1:', codi_canvis)
print(f'fet ({time.time() - T0:.0f} s)')

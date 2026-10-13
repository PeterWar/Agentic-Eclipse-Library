"""w6 · Rebut de la v2 del mapa MSB (12-10-2026): entrades amb SHA-256 (la cau es torna a hashejar), codi, constants, decisions,
proves i sortides amb SHA-256. Escriu v2/mapa/RECEIPT_mapa_v2.json. Només llegeix."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc          # noqa: E402
import msb_comu_v2 as m2       # noqa: E402

T0 = time.time()
M2 = m2.MAPA2
rel = lambda p: str(Path(p).resolve().relative_to(mc.ARREL)) if str(Path(p).resolve()).startswith(str(mc.ARREL)) else str(p)   # noqa: E731
cau = mc.troba_cau()
entrades = {}
for n in ('fusion_total_v42.npy', 'weight_vixen_v42.npy', 'support_v42.npy', 'var_vixen_v42.npy', 'var_sony_v42.npy'):
    h = mc.sha256(cau / n)
    entrades['cau/' + n] = dict(sha256=h, igual_que_B3_V42_FROZEN=(h == mc.SHA_CAU[n]))
for p in (mc.MAPA / 'CEL.json', mc.MAPA / 'ZONES.json', mc.MAPA / 'zona_lunar_gap.npz', mc.MAPA / 'massa_aire_graella.npz',
          mc.MAPA / 'ple' / 'flags_ple.npy', mc.MAPA / 'PROVES_P0.json', mc.MAPA / 'PROVES_P2.json', mc.MAPA / 'PROVES_P3.json',
          mc.RES / 'comparacions' / 'caselles_nostra.npz', mc.RES / 'comparacions' / 'lasco' / 'c2_caselles.npz',
          mc.RES / 'comparacions' / 'lasco' / 'LASCO.json', mc.RES / 'comparacions' / 'models_f' / 'F_KL1985_digitalitzat.json',
          mc.RES / 'zp_canal' / 'SENSIBILITAT_ZP.json', mc.RES / 'zp_canal' / 'ZP_CANAL.json', mc.CR3_MATRIU,
          mc._GEOF, mc._MARS, mc._ESTR, mc._ZPDIR / 'zp2.json', mc._ZPDIR / 'corona2.csv', mc._ZPDIR / 'final_solution.json'):
    entrades[rel(p)] = dict(sha256=mc.sha256(p))
vdh = Path('/private/tmp/claude-501/-Users-USUARI-Desktop-Eclipse/9e6b16f2-4b05-4c89-aaab-3a354c778218/scratchpad/rev10/fcorona/v-5.png')
font_vdh = dict(cita='van de Hulst, H. C. 1950, BAN 11, 135 (1950BAN....11..135V), p. 139, eqs. (5)-(9)', escaneig_ADS_fora_del_projecte=str(vdh),
                sha256=mc.sha256(vdh) if vdh.is_file() else None,
                llegit='K_max = 355,6 r^-17 + 177,8 r^-7 + 0,708 r^-2,5; K_min = 200,0 r^-17 + 100,0 r^-7 + 0,398 r^-2,5; '
                       'F = 14,86 r^-7 + 4,99 r^-2,5; K_pole = 191,0 r^-17 + 12,59 r^-7 (unitat: 1e-8 de la brillantor MITJANA del disc, p. 136)')
codi = {rel(p): mc.sha256(p) for p in sorted(mc.EINES.glob('w*.py')) + [mc.EINES / 'msb_comu_v2.py', mc.EINES / 'msb_comu.py',
                                                                       mc.EINES / 'comparacions' / 'cmp_comu.py', mc.EINES / 'executa.sh']}
sortides = {}
for p in sorted(M2.rglob('*')):
    if p.is_file() and p.name != 'RECEIPT_mapa_v2.json':
        sortides[rel(p)] = dict(sha256=mc.sha256(p), bytes=p.stat().st_size)
CEL = m2.coef_cel_v2()
W1 = json.load(open(m2.CELDIR / 'PROVES_W1.json'))
W3 = json.load(open(M2 / 'PROVES_W3.json'))
W4 = json.load(open(M2 / 'PROVES_W4.json'))
DIP = json.load(open(M2 / 'dipol_c2' / 'DIPOL_C2_v2.json'))
SOR = json.load(open(M2 / 'soroll' / 'SOROLL_BLOCS.json'))
rebut = {
    'encarrec': 'mapa MSB v2: correccions obligatòries dels verificadors v1 i v2 (rev10/calcul.json), part del mapa',
    'data': time.strftime('%Y-%m-%dT%H:%M:%S'), 'agent': 'Claude (flux del 12-10-2026)',
    'estat': 'PROVISIONAL: res no es publica ni s\'envia sense el sí de Pere (AGENTS §9)',
    'v1_intacta': 'cap fitxer de resultats/msb_calibrat_20261011/{mapa,comparacions,zp_canal,per_compartir,verificacio_xifres} s\'ha escrit',
    'cau_b3': dict(carpeta=str(cau), nota='Paperera de Pere, NOMÉS LECTURA (mmap)'),
    'entrades_sha256': entrades, 'font_van_de_Hulst_1950': font_vdh, 'codi_sha256': codi,
    'constants': dict(FAC_G=m2.FAC_G, X_ref_extincio=m2.X_REF, X_sol_DATE_OBS=W3['X_sol_date_obs'], K_EXT=m2.K_EXT, K_BANDA=m2.K_BANDA,
                      K_dipol=m2.K_DIPOL, punt_zero=W3['punt_zero'], sistematica_relativa_simetrica=m2.SIS_REL_SIM,
                      sistematica_constant_avall=W3['rel_lo'], sistematica_constant_amunt=W3['rel_hi'],
                      terra_cel_BSOL=m2.SIGMA_SKY_FLOOR_BSOL),
    'cel': dict(adoptat=CEL['adoptat'], motiu=CEL['motiu'], condicions=CEL['condicions_tria'], alternatives_sigma=CEL['alternatives_sigma'],
                models=CEL['models'], tria_escrita=W1['tria']['escrit_abans_del_quocient_C2'],
                predeclaracio='v2/mapa/PREDECLARACIO_CEL_v2.md (2026-10-11 23:45)', control_replica_v1=W1['control_replica_v1']),
    'proves': dict(control_dipol_v1=DIP['control_replica_v1'], wcs=W3['prova_wcs'], canvi_recompte_flags=W3['canvi_recompte'],
                   soroll_blocs=SOR['conclusio'], franja_lunar=W4['franja_lunar']),
    'xifres_clau': {k: dict(MSB=v['MSB'], MSB_v1=v['MSB_v1'], total_avall=v['total_avall'], total_amunt=v['total_amunt'],
                            biaix_cel=v['biaix_cel_un_sol_sentit']['central'], frac_sony=v['frac_sony'])
                    for k, v in W4['xifres_clau'].items()},
    'sortides_sha256': sortides,
}
json.dump(rebut, open(M2 / 'RECEIPT_mapa_v2.json', 'w'), indent=1, ensure_ascii=False, default=float)
print('rebut escrit:', len(sortides), 'sortides,', len(entrades), 'entrades; cau igual:',
      all(v.get('igual_que_B3_V42_FROZEN', True) for v in entrades.values()), f'({time.time() - T0:.0f} s)')

"""p5 · Rebut del mapa MSB (11-10-2026): entrades amb SHA-256, TOTES les constants, decisions, proves i sortides amb SHA-256.
Escriu mapa/RECEIPT_mapa.json. Només llegeix el que han escrit p0–p4."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc

M = mc.MAPA
P = {k: json.load(open(M / f'PROVES_{k}.json')) for k in ('P0', 'P1', 'P2', 'P3')}
CEL = mc.coef_cel()
rel = lambda p: str(Path(p).resolve().relative_to(mc.ARREL))
entrades = dict(P['P0']['entrades_sha256'])
for f in ('3-RECERCA/75_MESURES_16-08_RESOLUCIO_GUANY_I_CALIBRATGE_ABSOLUT.md', '3-RECERCA/76_HDR_CORONA_VIXEN_2026-08-16.md',
          '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/B3_V42_FROZEN.json',
          '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/b3_v42_dependencies/b3.py',
          '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/b3_v42_dependencies/comu.py',
          '3-RECERCA/tools/astrometria/xmatch/zp.py', '3-RECERCA/tools/astrometria/xmatch/corona2.py',
          '3-RECERCA/tools/comparacio_sdo_lasco_20261001/c9_brillantor.py', '3-RECERCA/tools/comparacio_sdo_lasco_20261001/comu_comp.py'):
    entrades[f] = dict(sha256=mc.sha256(mc.ARREL / f), us='constants o recepta citades (només lectura)')
codi = {rel(p): mc.sha256(p) for p in sorted(mc.EINES.glob('*.py')) + sorted(mc.EINES.glob('*.sh'))}
sortides = {}
for p in sorted(M.rglob('*')):
    if p.is_file() and p.name != 'RECEIPT_mapa.json':
        sortides[rel(p)] = dict(sha256=mc.sha256(p), bytes=p.stat().st_size)
clau = P['P3']['xifres_clau']
rebut = {
    'encarrec': 'mapa-msb: mapa calibrat de la corona en MSB (B/B☉) des del compost lineal; proposta rebuda en la revisió de l'article',
    'data': time.strftime('%Y-%m-%dT%H:%M:%S'), 'agent': 'Claude (flux de l\'11-10-2026)',
    'estat': 'PROVISIONAL: res no es publica ni s\'envia sense el sí de Pere (AGENTS §9)',
    'cau_b3': dict(carpeta=P['P0']['cau'], nota='Paperera de Pere, NOMÉS LECTURA (mmap); cap escriptura, moviment ni esborrat'),
    'entrades_sha256': entrades,
    'codi_sha256': codi,
    'constants': {
        'FAC_G_MSB_per_ADU_s_pixel_verd': mc.FAC_G, 'FAC_G_error_relatiu': mc.FAC_G_REL_ERR,
        'FAC_G_recalculat_de_zp2': mc.factor_des_de_zp(),
        'FAC_G_font': 'corona2.csv (r6): π·(947,07″/2,147827″/px)² / 10^(0,4·(ZP 14,2052 + 26,75 − 0,653·c 0,1488)); research/75 §5.2',
        'ZP_X_sol': mc.ZP_X_SOL, 'ZP_epoca_utc': mc.ZP_EPOCA_UTC,
        'K_ext_adoptat': mc.K_EXT, 'K_banda_sistematica': mc.K_BANDA,
        'massa_aire': dict(formula='Kasten–Young 1989: X = 1/(sin h + 0,50572·(h + 6,07995°)^−1,6364)', altura='aparent (refractada)',
                           refraccio=mc.REFRACCIO, data=mc.DATE_OBS, X_sol=P['P1']['massa_aire']['X_sol'],
                           h_sol=P['P1']['massa_aire']['h_sol_refractada'], X_sol_geometrica=P['P1']['massa_aire']['X_sol_geometrica'],
                           graella='astropy cada 64 px + spline bicúbica (mapa/massa_aire_graella.npz)'),
        'extincio': 'E = 10^(0,4·k·(X − X☉)), aplicada DESPRÉS de restar el cel',
        'DATE_OBS': mc.DATE_OBS, 'DATE_BEG_C2': mc.DATE_BEG, 'DATE_END_C3': mc.DATE_END, 'lloc': mc.LLOC,
        'geometria': dict(sol_xy=mc.SOL_XY, R_sol_px=mc.RSOL_PX, escala_arcsec_px=mc.SC, R_sol_arcsec=mc.RSOL_ARCSEC, P_deg=mc.P_DEG,
                          nord_solar=mc.NORD_SOLAR.tolist(), est_solar=mc.EST_SOLAR.tolist(), OFF_V121_a_llenc=mc.OFF.tolist(),
                          angle_nord_est_deg=P['P0']['geometria']['prova_geo']['angle_nord_est_deg'],
                          centres_alternatius=mc.SOL_ALTERNATIUS, lluna_xy_18_28_49=mc.LLUNA_XY, R_lluna_px=mc.R_LLUNA_PX),
        'zones': dict(R_banda_px=mc.R_BANDA_PX, gap_px=mc.GAP_PX, ghost_xy=mc.GHOST_XY, ghost_r_px=mc.GHOST_R_PX,
                      protuberancies_predeclarades=dict(PA=mc.PROM_PA, dPA=mc.PROM_DPA, rmax=mc.PROM_RMAX),
                      protuberancies_sectors_finals=mc.PROM_SECTORS, wv_sony=mc.WV_SONY,
                      R_inscrit_Rsol=mc.zones()['R_inscrit_Rsol']),
        'flags_bits': mc.BITS, 'flags_descripcio': mc.DESC_BITS, 'flags_exclosos_dels_perfils': mc.EXCLOU_PERFILS,
        'color': dict(M_R6=mc.M_R6.tolist(), WB_R6=mc.WB_R6.tolist(), guany_CIENCIA=mc.GUANY_CIENCIA.tolist(),
                      A_u_a_ucam=mc.matriu_inversa().tolist(), formula='u_cam = diag(1/wb)·M⁻¹·diag(1/g)·u; G_cam = A[1,:]·u'),
        'cel': CEL,
        'incerteses': dict(sistematica_relativa=mc.SIS_REL, sistematica_relativa_quadratura=mc.sis_rel_constant(),
                           extincio='max |10^(0,4·(k′ − 0,40)·(X − X☉)) − 1| per a k′ = 0,35 i 0,72',
                           cel='σ_sky = max(|S_a − S_b|, |S_c − S_b|, 1e-9 B☉ / FAC_G); en MSB × FAC_G × E',
                           estadistica=('σ = κ·√(wv²·vV + ws²·vS)·G_cam·FAC_G·E, amb vV i vS les variàncies relatives del DoG(1,5−3 px) de ln G '
                                        'de cada tren (b3.var_map, σ48 px), ws = 1 − wv on hi ha Sony; κ = 7,92 per a soroll blanc '
                                        '(cv2, mateix nucli que la b3). Agrupat 2×2: √(Σσ²)/4.'),
                           KAPPA_DOG=mc.KAPPA_DOG, halo='NO modelat ni inclòs (G3 obert); cota del C2: excés ×1,2–1,8 a 2,4–5,5 R☉'),
        'agrupacio_2x2': ('mitjana dels 4 píxels si tots 4 tenen dada (ni NO_DATA ni LIMB_GAP), si no NaN; σ_stat √(Σσ²)/4; σ_sys i σ_sky mitjana; '
                          'cel, massa d\'aire i pes Vixen: mitjana dels píxels del llenç; FLAGS: OR. Columna 10551 afegida com a NO_DATA (amplada senar)'),
    },
    'decisions_i_suposicions': [
        'Variable: verd natiu de la càmera (G_cam), on viu el punt zero de les estrelles; la luminància (G + kr·R)/2 de research/76 només com a control.',
        'Massa d\'aire amb altura APARENT i la refracció de zp.py (T 20 °C, P 930 hPa): és la convenció del punt zero (reprodueix X☉ = 6,024 a 0,001). '
        'Amb altura geomètrica X☉ = 6,105 (el «≈ 6,1» de l\'encàrrec); E canvia < 1,3 % dins 6 R☉ entre les dues convencions.',
        'E val 1 al centre del Sol a DATE-OBS (18:29:34). El punt zero es va avaluar a 18:29:18,6 (X☉ 6,024): la diferència (0,4 %) cau dins la deriva del ±4 %.',
        'Geometria de la c9 (centre per efemèride via la Lluna; eixos afins de mars_final.json girats per P), tal com demana l\'encàrrec.',
        'Franja lunar = píxels amb dada a menys de 496 px del centre lunar de les 18:28:49; la prova p0 confirma que conté tota la zona que la Lluna '
        'va tapar en algun moment de la totalitat (trajectòria d\'efemèride, 28,9 px) més l\'ala de 13,9 px.',
        'Buit del limbe = píxels amb dada a ≤ 2 px de la zona lunar sense dada: NaN.',
        'Sectors de protuberància eixamplats perquè cobreixin TOTS els graus amb excés de R/G > 10 % trobats per la prova p0 (tots dins la franja).',
        'Cel adoptat: constant + pla (b), predeclarat; els models a i c només per a la incertesa.',
        'σ_stat es deixa tal com es va predeclarar encara que la prova p3 mostra que és una cota alta (dispersió real 0,1–0,37 de σ_stat).',
        'El terme «color i cadena» (2,5 %) es manté: la reproducció de research/76 on el cel no mana (1,5 i 2 R☉) dona −1,8 % i +0,9 %.',
    ],
    'proves': {
        'hashes_igual_que_B3_V42_FROZEN': all(v.get('igual_que_B3_V42_FROZEN', True) for v in P['P0']['entrades_sha256'].values()),
        'color': P['P0']['color']['prova_color_cru_camera'], 'color_passa': P['P0']['color']['passa'],
        'geo_anada_tornada': P['P0']['geometria']['prova_geo'],
        'massa_aire_reprodueix_zp2': P['P0']['massa_aire_sol']['reprodueix_zp2'],
        'zenit': P['P0']['zenit'],
        'lluna': {k: P['P0']['lluna'][k] for k in ('longitud_C2_C3_px', 'ala_franja_px', 'franja_conte_tota_la_zona_tapada_mes_ala',
                                                     'pixels_tapats_fora_de_la_franja', 'vores_zona_sense_dada')},
        'cercle_inscrit': P['P0']['cercle_inscrit'],
        'protuberancies': P['P0']['protuberancies'],
        'spline_massa_aire': P['P1']['massa_aire']['prova_spline'],
        'variant_geometrica_massa_aire': P['P1']['massa_aire']['variant_geometrica'],
        'wcs_anada_tornada': P['P2']['prova_wcs'],
        'soroll_real_contra_sigma_stat': P['P3']['soroll'],
        'coherencia_research76': P['P3']['coherencia_research76'],
        'color_net_efecte_de_banda': P['P3']['color_net_efecte_de_banda'],
    },
    'xifres_clau': {k: {kk: v[kk] for kk in ('MSB', 'MSB_noext', 'sectors_10graus_amb_20px', 'sigma_sys_rel', 'sigma_geometria_rel',
                                            'sigma_cel_models_rel', 'MSB_cel_a', 'MSB_cel_c', 'cel_Bsun_mediana', 'frac_sony')}
                    for k, v in clau.items()},
    'extincio_vertical': {k: v for k, v in P['P1']['massa_aire'].items() if k.startswith('r')},
    'cel_Bsun': dict(al_centre=mc.FAC_G * CEL['b']['c0'], ADU_s=CEL['b']['c0'],
                     dispersio_models_p50_Bsun=P['P1']['cel']['dispersio_BSOL_p50']),
    'recompte_flags_ple': P['P2']['recompte_flags_ple'],
    'sortides_sha256': sortides,
    'pendents': [
        'Halo de la nostra òptica (G3): sense model; domina el dubte fora de ~2,5 R☉ juntament amb el cel.',
        'Incoherència entre trens (B_Vixen/B_Sony 0,83 contra 0,95): el mapa fora d\'1,9 R☉ és Sony·ρ en unitats Vixen; no s\'ha fet el mapa Sony independent.',
        'Zero contour del mapa amb colzes a la vora del camp Vixen (5–7 R☉): diferència petita de nivell de cel entre trens heretada de la fusió; no mesurada.',
        'Sense pB: el mapa és brillantor total K+F; la comparació amb el K-Cor necessita un model de p i de la corona F.',
        'Banda del C2 Orange (540–640 nm): el mapa és el verd de la càmera; cal la prova per canal (agent zp_canal) abans de fer una banda sintètica.',
    ],
}
json.dump(rebut, open(M / 'RECEIPT_mapa.json', 'w'), indent=1, ensure_ascii=False, default=float)
print('rebut escrit:', len(sortides), 'sortides,', len(entrades), 'entrades')

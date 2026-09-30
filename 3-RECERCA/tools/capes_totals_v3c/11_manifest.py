"""Manifest propi de V3c (per capa: centre i radi lunars, rang vàlid, rampes, porta lunar, P3/P4, tests, hashes) i
LLEGEIX-ME en català, escrits no-clobber a Documentacio i QA/V3c (el manifest del builder ja hi és: s'hi afegeix un sufix)."""
import hashlib
from pathlib import Path
from v3c_lib import *
DEST = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
DOC = DEST / 'Documentacio i QA/V3c'
cand = DEST / 'CapesTotalsV3c.psb'
ver = json.load(open(f'{SCR}/QA/verify_v3c.json')); bman = json.load(open(DOC / 'CapesTotalsV3c.manifest.json'))
fon = json.load(open(f'{SCR}/QA/fonament_disseny.json')); prot = json.load(open(f'{SCR}/QA/proteccio_P3_P4.json'))
cad = json.load(open(f'{SCR}/QA/cadena/cadena.json')); ell = json.load(open(f'{SCR}/lluna_ellipse_llenc.json')); rang = json.load(open(f'{SCR}/rang.json'))
res_f = json.load(open(f'{SCR}/QA/fonament/resum.json')); nuc = json.load(open(f'{SCR}/QA/final/nuclis_P3_P4_final.json'))
abans = json.load(open(f'{SCR}/QA/ABANS_mascara_ID5_sectors.json')); despres = json.load(open(f'{SCR}/QA/final/DESPRES_mascara_ID5_sectors.json'))
def rv(i):
    rows = rang[str(i)]; return dict(primer_anell_valid_Rsun=min(r['r'] for r in rows if r['p50'] <= 0.46 and r['p95'] <= 0.66), ultim_anell_SNR10_Rsun=max(r['r'] for r in rows if r['snr'] >= 10), ultim_anell_SNR5_Rsun=max(r['r'] for r in rows if r['snr'] >= 5))
layers = {}
for i, nom in ((3, '12_1/3200'), (4, '11_1/500'), (5, '10_1/125'), (7, '09_1/60'), (8, '08_1/30'), (9, '07_1/15'), (10, '06_1/8')):
    e = ell[str(i)]
    L = dict(nom=nom, centre_lunar_llenc=[round(e['cx'], 2), round(e['cy'], 2)], ellipse_a_b_theta=[round(e['a'], 2), round(e['b'], 2), round(e['theta_deg'], 2)], R_eq_px=round(R_eq(e), 2), rms_limbe_px=round(e['rms'], 2))
    if str(i) in rang: L['rang_valid'] = rv(i)
    if i == 3: L.update(veredicte='NO_TOCADA', mascara='blanca (font)', nota='base; autoritat de P3 (perles/diamant)')
    elif i in (4, 5, 7):
        f = fon[str(i)]
        L.update(veredicte='FONAMENT_REDERIVAT', rampa_pujada_Rsun=f['rampa_pujada'], delta_Rsun=f.get('delta'), w_max=f.get('w_max', 1.0), rampa_baixada=f['rampa_baixada'],
                 porta_lunar=dict(zero_fins_R_mes_px=f['porta_lunar']['core_px'], ploma_px=f['porta_lunar']['feather_px'], tipus='el·lipse pròpia, smootherstep radial'),
                 proteccio=f['proteccio'], mask_sha256_u16=f['mask_sha256_u16'], mask_max=f['mask_max'], alpha_max_disc_propi=f['alpha_max_disc_propi_R+2'], alpha_max_P3=f['alpha_max_P3'], alpha_max_P4=f['alpha_max_P4'],
                 cerca=f.get('cerca'), tests=res_f[str(i)])
        if i == 7: L['alpha_dins_banda_apilat_pct'] = dict(max=f['alpha_max_dins_banda_apilat_pct'], mitjana=f['alpha_mean_dins_banda_apilat_pct'])
    elif str(i) in cad:
        c = cad[str(i)]
        L.update(veredicte=c['veredicte'], r_a_Rsun=c['r_a'], r_b_Rsun=c.get('r_b'), delta_Rsun=c.get('delta'), w_max=c.get('w_max'), mask_sha256_u16=c.get('mask_sha256_u16'), porta=c.get('porta'), cobertura_bad=c.get('cobertura_bad'), sectors_sots=c.get('sectors_sots'), provats=c.get('provats'),
                 porta_lunar='banda per membre de l\'apilat (478 px de cada centre, ploma 20 px), com a V3b' if c['veredicte'] == 'ACCEPTADA' else 'màscara crua CT1 (oculta)')
    layers[str(i)] = L
layers['9'].update(veredicte='REBUTJADA', nota='15 combinacions (r_a 1,43 i 1,6; Δ 0,5–1,6; w 1,0–0,35): sempre mínims nous ≥1 % als sectors 225–255° (1,35–2,4 R☉) o al peu de la rampa (sector 150°); millor cas Δ1,6 w0,35: 2 defectes d\'1,3–1,4 % a 2,4 R☉ — la mateixa causa R12 de research/87 §11.2')
layers['10'].update(veredicte='REBUTJADA', nota='una passada (6 combinacions): mínims de 120–360 %')
man = dict(
    fitxer=str(cand), bytes=ver['size_v3c'], sha256=ver['sha256_v3c'], variant='V3c', data='2026-08-21',
    fonts_pinades=dict(corretgint2='1777d41f29e9644faae527c1b4aed3be25f3ff1079f1418aabbcc58d9109e052', capes_totals_v1='4d0480f1d6508c225f5dbb13fb5c4e608d35a07b58acc2625853284ba48f2a28'),
    offsets=bman['offsets']['applied'], builder_manifest=str(DOC / 'CapesTotalsV3c.manifest.json'),
    geometria=dict(llenc=[CW, CH], sol_llenc=list(SUN), R_sun_px=R_SUN, v_lluna_px_s=list(V_MOON)),
    defecte_ABANS=dict(mascara_ID5_Corretgint2_sectors_452_470=abans['452-470'], mascara_ID5_470_500=abans['470-500'], resum='forat entre 165° i 210° (0,000–0,19 a 452–470 px contra ~0,33 a la resta; 0,014 a 470–500 contra ~0,82); sots a 90° i 255°'),
    despres=dict(mascara_ID5_452_470=despres['mascara_ID5_452-470'], mascara_ID5_470_500=despres['mascara_ID5_470-500'], resum=despres['mascara_ID5_470-500_resum']),
    proteccio=prot, nuclis_final=nuc,
    capes=layers,
    tests=dict(definicions=dict(
        porta_costura='mínims nous al DESPRÉS (no a ABANS ni a la capa) ≥1 % ∧ ≥3σ ∧ ≥10 px, perfils lunar-cèntrics fins R+0,3 R☉+60 px i solars 1–4,6 R☉ (defecte només ≤3 R☉), global + 24 sectors; V1 (cap mínim al perfil lunar global); empremta no radial = rms del compost amb màscara radialitzada (mitjana per anell solar d\'α/porta lunar) des de R+3, excloent només P3/P4 amb ploma, ≤0,5 %; nuclis i disc propi 0 DN; fora del suport 0 DN',
        cobertura='cel·les 4 px × 5° lunar-cèntriques R+3 → 1,5 R☉ i 0,05 R☉ × 15° solars 1,5 → 3 R☉; capa vàlida a la cel·la si p50≤0,46 i p95≤0,66 del canal màxim i r ≤ últim anell amb SNR≥5; suma de pesos Normal efectius de les capes vàlides ≥0,9; s\'exclouen els píxels de P3/P4',
        sectors_absolut='mediana lunar-cèntrica per cel·la (8 px × 5°, R+3 → R+120); SOT si < 0,85 × mediana dels 4 veïns de cada costat, la capa vàlida més alta és la mateixa a tots i el sot no és a la pròpia capa (compost/capa < 0,9); exclou cel·les amb >30 % de P3/P4'),
        fonament=res_f, cadena={k: {kk: vv for kk, vv in v.items() if kk != 'provats'} for k, v in cad.items()}),
    verificacio=dict(ok=ver['ok'], merged_vs_offline_DN=ver['merged_vs_offline_DN'], merged_vs_cadena_DN=ver['merged_vs_cadena_DN'], capes={k: dict(ok=v['ok'], visible=v['visible'], raster_equal_v3b=v['raster_equal_v3b'], mask_bbox=v['mask_bbox']) for k, v in ver['layers'].items()}),
    reserves=[
        'Cobertura: 24 cel·les (de 3.765) a 135–150° entre R+43 i R+55 i R+115..127 queden a 0,85–0,90 perquè al nucli del streamer brillant la 1/125 (i la 1/60) té p50 0,47–0,54 (>0,46) amb un pes ≤0,15: compressió lleu del revelat, no forat de cobertura; r_a per anell (research/84 §5). Amb r_a per cel·les (1,133/1,297 R☉) el fonament passa la cobertura però cap capa 8/9 no passa la porta.',
        'R12: les capes no estan normalitzades per exposició (q≈2–3,3 entre capes consecutives); per això 1/60 necessita Δ=0,9 R☉, 1/30 entra amb pes 0,5 i 1/15 i 1/8 no passen la porta sobre aquest fonament. Mateixa conclusió que research/87 §11.2: normalitzar l\'escala abans de compondre és decisió de Pere.',
        'Banda d\'artefacte de l\'apilat 1/60: no mesurable (V3b); porta de fotograma únic; la rampa radial hi posa α ≤0,32 % → irrellevant.',
        'Els ràsters d\'ID4/ID5 (llenç sencer) tenen vora blanca fora de la imatge: les màscares noves són 0 fora de (457,463)-(7417,5103).'])
out = DOC / 'CapesTotalsV3c.manifest_v3c.json'
if out.exists(): raise SystemExit(f'existeix: {out}')
jdump(man, out); print('manifest', out)

"""11 — Manifest propi de V4 + LLEGEIX-ME, no-clobber a la documentació de la variant.
Agrupa: decisions §8, revelats (RENDER_RECEIPT), re-calibratge §4.2, el·lipses, P3/P4, rang,
disseny del fonament, cadena sencera amb veredictes, tests i verificació reoberta."""
import json, hashlib
from pathlib import Path
from v4_lib import *

DEST = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
import os
TAG = os.environ.get('V4TAG', 'V4b')
DOC = DEST / 'Documentacio i QA' / TAG
cand = DEST / f'CapesTotals{TAG}.psb'
ver = json.load(open(V4W / 'QA/verify_v4.json'))
bman = json.load(open(DOC / f'CapesTotals{TAG}.manifest.json'))
fon = json.load(open(V4W / 'QA/fonament_disseny.json'))
prot = json.load(open(V4W / 'QA/proteccio_P3_P4.json'))
cad = json.load(open(V4W / 'QA/cadena/cadena.json'))
ell = ell_all()
rang = rang_all()
res_f = json.load(open(V4W / 'QA/fonament/resum.json'))
nuc = json.load(open(V4W / 'QA/final/nuclis_P3_P4_final.json'))

def rv(i):
    rows = rang[str(i)]
    v = [r['r'] for r in rows if r.get('sat_frac', 1) <= 0.5 and r.get('snr', 0) >= 5]
    plat = [r['r'] for r in rows if r.get('sat_frac', 0) >= 0.5]
    return dict(primer_anell_valid_Rsun=min(v) if v else None,
                plateau_anell_des_de=min(plat) if plat else None,
                ultim_anell_SNR5_Rsun=max([r['r'] for r in rows if r.get('snr', 0) >= 5] or [None]))

layers = {}
for i in ORDER:
    e = ell[str(i)]
    L = dict(prefix=LAYER_PREFIX[i], centre_lunar_llenc=[round(e['cx'], 2), round(e['cy'], 2)],
             ellipse_a_b_theta=[round(e['a'], 2), round(e['b'], 2), round(e['theta_deg'], 2)],
             R_eq_px=round(R_eq(e), 2), rang_valid=rv(i))
    if i == 3:
        L.update(veredicte='BASE', mascara='blanca (font)', nota='autoritat de P3 (perles/diamant)')
    elif i in (4, 5, 7):
        f = fon[str(i)]
        L.update(veredicte='FONAMENT_REDERIVAT_V4', rampa_pujada_Rsun=f['rampa_pujada'], w_max=f.get('w_max', 1.0),
                 mask_sha256_u16=f['mask_sha256_u16'], alpha_max_P3=f['alpha_max_P3'], alpha_max_P4=f['alpha_max_P4'],
                 tests=res_f[str(i)])
    elif str(i) in cad:
        c = cad[str(i)]
        L.update(veredicte=c['veredicte'], r_a_Rsun=c.get('r_a'), r_b_Rsun=c.get('r_b'), w_max=c.get('w_max'),
                 mask_sha256_u16=c.get('mask_sha256_u16'), porta=c.get('porta'),
                 cobertura_bad=c.get('cobertura_bad'), sectors_sots=c.get('sectors_sots'))
    layers[str(i)] = L

man = dict(
    fitxer=str(cand), bytes=ver['size_v4'], sha256=ver['sha256_v4'], variant='V4', data='2026-08-21',
    proposta='PROPOSTA_Normalitzacio_Exposicio_CapesTotalsV4.md · decisions §8 signades per Pere: '
             'Opcio A→B+ (renderer offline: ACR scriptat no dona 16 bits a PS 27.9.1); t_ref=1/15 s; '
             'capa 01 = 10,08 s fotomètric; contracte a postprocessat-corona v3; V3c congelada',
    revelat=dict(eina='research/tools/revelat_normalitzat/render_lineal.py v1',
                 pipeline='LinearRaw -> (x-negre)/(blanc-negre) -> WB As Shot -> x t_ref/t -> FM2 D65 -> '
                          'Bradford D65 -> Display P3 lineal -> TRC sRGB -> u16',
                 receipts='Derivats/Vixen/HDR4/revelat_v4/receipts/v4_*.receipt.json',
                 baseline_exposure='0,26 present als 12 DNG, NO aplicat',
                 wb='As Shot idèntic als 12 fitxers (neutral 0.514573 1 0.602707)'),
    recalibratge_4_2=dict(
        validesa='sat_frac ≤ 0,5 (plateau del sensor, raw ≥ blanc) + SNR ≥ 5; p50/p95 del codificat '
                 'queden com a diagnòstic (mesuraven la corba ACR, que la V4 no té)',
        P3='clip blanc de la 1/3200 (fenòmens que clippen a TOTES les capes), components ≥3 px, anell 400–600 px',
        P4='clip blanc de la 1/500 (R+64) ∪ excés vermell ∪ limbe R→R+4',
        factor_sat_cadena='(1 − sat_i) amb ploma 1+2 px: una capa no contribueix on és saturada',
        domini_porta_extern='perfils solars i defectes fins a r_b+marge (mateixos llindars §9.4)'),
    fonts_pinades=dict(corretgint2='1777d41f29e9644faae527c1b4aed3be25f3ff1079f1418aabbcc58d9109e052',
                       capes_totals_v1='4d0480f1d6508c225f5dbb13fb5c4e608d35a07b58acc2625853284ba48f2a28'),
    offsets=bman['offsets']['applied'],
    geometria=dict(llenc=[CW, CH], sol_llenc=list(SUN), R_sun_px=R_SUN, v_lluna_px_s=list(V_MOON)),
    proteccio=prot, nuclis_final=nuc, capes=layers,
    tests=dict(fonament=res_f,
               cadena={k: {kk: vv for kk, vv in v.items() if kk != 'provats'} for k, v in cad.items()}),
    verificacio=dict(ok=ver['ok'], merged_vs_offline_DN=ver['merged_vs_offline_DN'],
                     merged_vs_cadena_DN=ver['merged_vs_cadena_DN'],
                     capes={k: dict(ok=v['ok'], visible=v['visible'], raster_equal_render=v['raster_equal_render_v4'])
                            for k, v in ver['layers'].items()}))
out = DOC / f'CapesTotals{TAG}.manifest_v4.json'
if out.exists():
    raise SystemExit(f'existeix: {out}')
jdump(man, out)
print('manifest', out)

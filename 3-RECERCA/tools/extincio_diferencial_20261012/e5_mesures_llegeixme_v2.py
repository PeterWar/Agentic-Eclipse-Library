"""e5 · Mesures per al LLEGEIX-ME_v2 (12-10-2026). Les tres correccions que va demanar el verificador, amb la font de cada xifra.

No refà cap vista ni toca cap entrada. Llegeix:
  - les vistes P1_A i P1_B (JPEG que mira Pere; es comprova que el SHA és el del rebut v1);
  - E1_MASSA_AIRE_FINAL.json i E3_PIS2.json (resultats d'e1 i e3);
  - els registres de capa de la V125-FINAL.psb (només capçaleres, sense píxels; capes_psb.py de l'auditoria del whitepaper).
Escriu 3-RECERCA/resultats/extincio_diferencial_20261012/E5_MESURES_LLEGEIXME_v2.json.

1. Pis 1: diferència mitjana de gris (verd, 0–255) entre la meitat del zenit i la de l'horitzó, a la vista A i a la B, per anells.
   Píxels: amb dada (no el blau pissarra), fora de la franja del moviment lunar (< 496 px del centre lunar) i del fantasma de la Sony.
   Meitats: cos(PA − PA_zenit) > 0 o < 0, com a e2.
2. Pis 2: el canvi del color CODIFICAT (R/G i B/G) per meitats, el B/G de la corona sobre el cel estimat, i el residu del cel
   ajustat (E3, recepta.cel.residu_mediana_lin_menys_cel_sobre_cel_G).
3. Xifres petites: la banda de k (0,35–0,72) a 4 R☉ cap a l'horitzó; el factor global entre X☉ = 6,053 i ZPXSUN = 6,024 (mapa v2);
   i si la V125-FINAL porta alguna capa «07 SOBRE L'ATMOSFERA» (l'única que fa servir el vector EXTINCIO de comu.py)."""
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ed_comu as ed            # noqa: E402

mc = ed.mc
T0 = time.time()
REBUT_V1 = ed.SORT / 'REBUT_extincio_diferencial.json'
ALT_ROTOL = 186                       # franja de text de amb_rotol a 3000 px: int(54·1,5 + 37·1,5 + 50)
ANELLS_P1 = [(1.2, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0)]

rebut1 = json.load(open(REBUT_V1))
E1 = json.load(open(ed.RES / 'E1_MASSA_AIRE_FINAL.json'))
E3 = json.load(open(ed.RES / 'E3_PIS2.json'))
PAZ = E1['zenit']['PA_solar_deg']['r1']

# ------------------------------------------------------------------------------------------------ 1. pis 1, des dels JPEG
vistes = {}
for nom in ('P1_A_compost_lineal_sense_correccio.jpg', 'P1_B_compost_lineal_amb_correccio.jpg'):
    p = ed.SORT / nom
    sha = ed.sha256(p)
    esperat = rebut1['sortides'][ed.rel(p)]['sha256']
    assert sha == esperat, f'{nom}: el SHA no és el del rebut v1'
    im = np.asarray(Image.open(p).convert('RGB'), np.float64)[ALT_ROTOL:]
    vistes[nom] = dict(arr=im, sha256=sha)
imA = vistes['P1_A_compost_lineal_sense_correccio.jpg']['arr']
imB = vistes['P1_B_compost_lineal_amb_correccio.jpg']['arr']
h, w = imA.shape[:2]
assert (w, h) == (3000, 2134), (w, h)
W, H = mc.W, mc.H
xs = (np.arange(w) + 0.5) * W / w - 0.5               # centre de cada píxel de la vista al llenç V42
ys = (np.arange(h) + 0.5) * H / h - 0.5
XX, YY = np.meshgrid(xs, ys)
g = mc.geo_llenc()
r, pa = g.polar(XX, YY)
rm = np.hypot(XX - mc.LLUNA_XY[0], YY - mc.LLUNA_XY[1])
ghost = np.hypot(XX - mc.GHOST_XY[0], YY - mc.GHOST_XY[1]) < mc.GHOST_R_PX
gris = lambda a: (np.abs(a[..., 2] - a[..., 0]) < 8) & (np.abs(a[..., 1] - a[..., 0]) < 8)   # el blau pissarra no és gris
ok = gris(imA) & gris(imB) & (rm >= mc.R_BANDA_PX) & ~ghost
dz = np.cos(np.radians(pa - PAZ))
pis1 = []
for a, b in ANELLS_P1:
    m = ok & (r >= a) & (r < b)
    zA, hA = imA[..., 1][m & (dz > 0)].mean(), imA[..., 1][m & (dz < 0)].mean()
    zB, hB = imB[..., 1][m & (dz > 0)].mean(), imB[..., 1][m & (dz < 0)].mean()
    pis1.append(dict(r=[a, b], n_zenit=int((m & (dz > 0)).sum()), n_horitzo=int((m & (dz < 0)).sum()),
                     A_zenit=zA, A_horitzo=hA, B_zenit=zB, B_horitzo=hB,
                     diferencia_zenit_menys_horitzo_A_DN=zA - hA, diferencia_zenit_menys_horitzo_B_DN=zB - hB))
    print(f'pis 1, {a}–{b} R☉: zenit − horitzó  A {zA - hA:5.1f} DN → B {zB - hB:5.1f} DN', flush=True)

# ------------------------------------------------------------------------------------------------ 2. pis 2, des d'E3
pis2_color = []
for f in E3['balanc_per_canal']:
    if f['zona'] == 'anell':
        continue
    ca, cd = f['codificat_abans'], f['codificat_despres']
    pis2_color.append(dict(r=f['r'], zona=f['zona'], E_mitjana=f['E_mitjana'],
                           RG_codificat_canvi_pc=100 * (cd['R_G'] / ca['R_G'] - 1),
                           BG_codificat_canvi_pc=100 * (cd['B_G'] / ca['B_G'] - 1),
                           BG_corona_sobre_cel=f['corona_abans']['B_G'], RG_corona_sobre_cel=f['corona_abans']['R_G'],
                           BG_lineal_total=f['lineal_abans']['B_G']))
for f in pis2_color:
    print(f"pis 2, {f['r']} {f['zona']:15s}: R/G cod {f['RG_codificat_canvi_pc']:+.2f} %  B/G cod {f['BG_codificat_canvi_pc']:+.2f} %"
          f"  | B/G corona {f['BG_corona_sobre_cel']:+.4f}", flush=True)
residu = E3['recepta']['cel']['residu_mediana_lin_menys_cel_sobre_cel_G']
# on són les zones «dalt_centre» i «baix_centre» d'e3 (300 files de la vora, ±600 px del centre del Sol), en R☉ i en PA
gf = ed.geo_final()
zones_residu = {}
for nom, (ya, yb) in (('dalt_centre', (0, 300)), ('baix_centre', (ed.HF - 300, ed.HF))):
    yy, xx = np.meshgrid(np.arange(ya, yb, 10.0), np.arange(gf.cx - 600, gf.cx + 600, 10.0), indexing='ij')
    rr, pp = gf.polar(xx, yy)
    zones_residu[nom] = dict(r_Rsol=[float(rr.min()), float(rr.max())], r_mediana=float(np.median(rr)),
                             PA_mediana=float(np.median(pp)), dPA_del_zenit=float(abs((np.median(pp) - PAZ + 180) % 360 - 180)))
print('zones del residu:', {k: (round(v['r_mediana'], 2), round(v['dPA_del_zenit'], 1)) for k, v in zones_residu.items()}, flush=True)
canvi4 = [f for f in E3['canvi_visible_sectors_15graus'] if f['r'] == 4.0][0]
canvi3 = [f for f in E3['canvi_visible_sectors_15graus'] if f['r'] == 3.0][0]
print('residu del cel (lin − cel)/cel, verd:', {k: round(v, 4) for k, v in residu.items()}, flush=True)

# ------------------------------------------------------------------------------------------------ 3. xifres petites
f4 = [f for f in E1['eix_zenit'] if f['r_Rsol'] == 4.0][0]
dX4 = f4['horitzo']['X'] - E1['X_sol']
banda_k = {f'{k:.2f}': ed.factor_E(f4['horitzo']['X'], E1['X_sol'], k=k) for k in (0.35, 0.40, 0.72)}
global_zp = float(10 ** (0.4 * ed.K * (E1['X_sol'] - mc.ZP_X_SOL)))
print(f'4 R☉ horitzó: ΔX {dX4:.4f}; E per k 0,35/0,40/0,72: {banda_k}; factor X☉ 6,053 contra ZPXSUN {mc.ZP_X_SOL:.4f}: {global_zp:.4f}',
      flush=True)
AUD = ed.ARREL / 'publicacions/whitepaper/revisio_pere_20260923/revisio_8/auditoria'
sys.path.insert(0, str(AUD))
import capes_psb               # noqa: E402  (només registres de capa; lectura pura)
cp = capes_psb.llegeix(str(ed.PSB))
noms = [c.get('nom', '') for c in cp['capes']]
atmos = [n for n in noms if 'ATMOSF' in n.upper() or 'EXTINCI' in n.upper()]
print(f'V125-FINAL: {len(noms)} registres de capa; amb «ATMOSF» o «EXTINCI» al nom: {atmos}', flush=True)

out = dict(
    guio=ed.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    per_a='LLEGEIX-ME_v2.md (les tres correccions del verificador i les xifres petites)',
    pis1_vistes=dict(fitxers={k: v['sha256'] for k, v in vistes.items()}, iguals_al_rebut_v1=True,
                     criteri='verd del JPEG (0–255) sota la franja de text; píxels grisos (amb dada), fora de la franja lunar i del '
                             'fantasma; meitats per cos(PA − PA_zenit)', PA_zenit=PAZ, anells=pis1),
    pis2_color_per_meitats=pis2_color,
    pis2_residu_cel_G=dict(font='E3_PIS2.json recepta.cel.residu_mediana_lin_menys_cel_sobre_cel_G', valors=residu,
                           definicio='mediana de (lineal − cel ajustat)/cel ajustat al verd; dalt_centre i baix_centre: 300 files de '
                                     'la vora, ±600 px del centre del Sol', zones=zones_residu),
    pis2_sector_horitzo_3_i_4_Rsol=dict(r3=canvi3['horitzo'], r4=canvi4['horitzo']),
    banda_k_4Rsol_horitzo=dict(dX=dX4, E=banda_k),
    factor_global_Xsol_contra_ZPXSUN=dict(X_sol=E1['X_sol'], ZPXSUN=mc.ZP_X_SOL, factor=global_zp),
    capes_V125_FINAL=dict(eina=ed.rel(AUD / 'capes_psb.py'), n_registres=len(noms), amb_atmosfera_o_extincio=atmos),
    segons=round(time.time() - T0, 1))
ed.json_dump(out, ed.RES / 'E5_MESURES_LLEGEIXME_v2.json')
print(f'fet ({time.time() - T0:.0f} s)')

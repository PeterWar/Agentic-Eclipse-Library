"""v4b · Vistes de la V128 NOVA (regla del limbe, 12-10-2026), amb noms nous a Sortides/v128_extincio_20261012/.
Llenç SENCER, a la meitat (3967 px d'ample), JPEG amb el perfil Adobe RGB de la final incrustat; cap retall.
Les fusionades es llegeixen dels FITXERS (V125-FINAL.psb i V128.psb, lector cru, sense Photoshop), com el v4:
  b01 · la fusionada de la V125-FINAL, tal com és (ha de sortir idèntica a la 01 del v4);
  b02 · la fusionada de la V128 nova (= la capa A nova encesa);
  b03 · el quocient V128 / V125 en lluminància lineal, amb les isolínies d'E, el zenit i 1,5 i 4 R☉; sense color on la regla
        no toca res (r < 440 px, i a l'anell 440–470 px els píxels idèntics a la V125: el disc fosc, sense dada);
  b04 · els tres de costat, petits i amb rètols a sobre (els rètols no tapen cap píxel del llenç);
  b05 · EN LLOC DE RETALLS, un gràfic del perfil radial a través del limbe (dades del v1b, PERFIL_LIMBE_V128B.npz, calculades
        de les matrius que el v3b ha comprovat iguals al fitxer): lluminància i cel, quocient V128/V125 de la capa anterior i
        de la nova cap al zenit i cap a l'horitzó, i la fracció de la correcció aplicada als 29 sectors de 10° avaluats.
        PNG amb el perfil Adobe RGB incrustat (el gràfic es fa en sRGB i s'hi passa, com el panell 03).
Ús: PYTHONDONTWRITEBYTECODE=1 <python> v4b_vistes.py <V128.psb> <carpeta_de_treball> [carpeta_d_esborrany]
    (sense el 3r argument, escriu a Sortides/ i no hi sobreescriu res)"""
import hashlib
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

AQUI = Path(__file__).resolve().parent
ARREL = AQUI.parents[2]
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/extincio_diferencial_20261012'))
import psb_cru as pc  # noqa: E402
import ed_comu as ed  # noqa: E402

T0 = time.time()
mc = ed.mc
SRC = ARREL / '1-PHOTOSHOP/V125-FINAL.psb'
DST = Path(sys.argv[1]).resolve()
TREB = Path(sys.argv[2]).resolve()
TREB.mkdir(parents=True, exist_ok=True)
SORT = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else ARREL / 'Sortides/v128_extincio_20261012'   # 3r arg: esborrany
RES = ARREL / '3-RECERCA/resultats/v128_extincio_20261012'
SORT.mkdir(parents=True, exist_ok=True)
AMPLE = 3967
NOMS = dict(b01='b01_V125-FINAL_fusionada.jpg', b02='b02_V128_fusionada_limbe_per_dada.jpg',
            b03='b03_quocient_V128_sobre_V125_limbe_per_dada.jpg', b04='b04_costat_a_costat_limbe_per_dada.jpg',
            b05='b05_perfil_radial_del_limbe.png')
for n in NOMS.values():
    assert not (SORT / n).exists(), f'{n} ja existeix: no se sobreescriu'
v1b = json.load(open(RES / 'V1B_CORRECCIO_LIMBE.json'))
R_INT, R_EXT = v1b['regla']['R_INT'], v1b['regla']['R_EXT']


def fusionada(ruta):
    p = pc.PSB(ruta)
    H, W, n = p.alt, p.ample, p.alt * p.ample * 2
    assert p.id_compressio == 0
    a = np.stack([np.frombuffer(p.b, '>u2', H * W, p.id_pos + 2 + k * n).reshape(H, W) for k in range(3)], -1).astype(np.uint16)
    icc = [bytes(p.b[r['dades']:r['dades'] + r['mida']]) for r in p.recursos if r['id'] == 1039][0]
    p.tanca()
    return a, icc


U, icc = fusionada(SRC)
V, icc2 = fusionada(DST)
assert icc == icc2
fus_igual_OUTB = hashlib.sha256(np.ascontiguousarray(V).tobytes()).hexdigest() == v1b['matriu']['sha256_bytes_OUTB']
assert fus_igual_OUTB, 'la fusionada del fitxer no és la matriu del v1b'
H, W = U.shape[:2]
ii = ed.info_icc(icc)
YC = np.array(ii['Y'])
print(f'fusionades llegides ({time.time() - T0:.0f} s)', flush=True)


def vista(a16):
    return Image.fromarray((np.clip(np.stack([ed.redueix_float(a16[..., c].astype(np.float32) / 65535.0, AMPLE)
                                              for c in range(3)], -1), 0, 1) * 255 + 0.5).astype(np.uint8))


imA, imB = vista(U), vista(V)
ed.desa_jpeg(imA, SORT / NOMS['b01'], icc)
ed.desa_jpeg(imB, SORT / NOMS['b02'], icc)
print(f'b01 i b02 ({imA.size}) ({time.time() - T0:.0f} s)', flush=True)

# quocient de lluminància lineal, per blocs de la mida de la vista
hh = int(round(H * AMPLE / W))
Ya = cv2.resize((((U.astype(np.float64) / 65535.0) ** ed.GAMMA) @ YC).astype(np.float32), (AMPLE, hh), interpolation=cv2.INTER_AREA)
Yd = cv2.resize((((V.astype(np.float64) / 65535.0) ** ed.GAMMA) @ YC).astype(np.float32), (AMPLE, hh), interpolation=cv2.INTER_AREA)
quoc = Yd / np.maximum(Ya, 1e-9)
# on la regla no toca res: r < R_INT, i a l'anell els píxels idèntics a la V125 (a resolució plena)
LX, LY = ed.LLUNA_F
yy_, xx_ = np.mgrid[0:H, 0:W]
rl_full = np.hypot(xx_ - LX, yy_ - LY)
del yy_, xx_
intacte = (rl_full < R_INT) | ((rl_full <= R_EXT) & np.all(V == U, axis=2))
del rl_full
mask_v = cv2.resize(intacte.astype(np.float32), (AMPLE, hh), interpolation=cv2.INTER_AREA) > 0.5
del intacte
escala = W / AMPLE
xs = (np.arange(AMPLE) + 0.5) * escala - 0.5
ys = (np.arange(hh) + 0.5) * (H / hh) - 0.5
sp = ed.Spline(ed.GRAELLA_FINAL)
Ev = ed.factor_E(sp.X_graella(ys, xs), sp.X_sol).astype(np.float32)
XX, YY = np.meshgrid(xs, ys)
qv = np.where(mask_v, np.nan, quoc)
fons = 0.75 * (Ya ** (1 / ed.GAMMA))
g = ed.geo_final()
geoV = mc.Geo(g.cx, g.cy, g.R, g.n, g.e)
E1 = json.load(open(ed.RES / 'E1_MASSA_AIRE_FINAL.json'))
PAZ = E1['zenit']['PA_solar_deg']['r1']
tmp = TREB / 'v4b_03_srgb.png'
ed.panell_factor(fons, qv, Ev, geoV, escala, PAZ, tmp, ample=AMPLE, etiqueta='lluminància lineal: V128 / V125', r_fletxa=4.5, r_text=5.05)
imC = ed.srgb_a_adobe(Image.open(tmp), icc)
if imC.size != imA.size:
    imC = imC.resize(imA.size, Image.LANCZOS)
ed.desa_jpeg(imC, SORT / NOMS['b03'], icc)
print(f'b03 ({time.time() - T0:.0f} s)', flush=True)

mig = 1500


def petit(im, t, s):
    return ed.amb_rotol(im.resize((mig, int(round(im.height * mig / im.width))), Image.LANCZOS), t, s, destacat=(255, 200, 80))


ed.desa_jpeg(ed.costat_a_costat([petit(imA, 'A · V125-FINAL (fusionada)', 'tal com és'),
                                  petit(imB, 'B · V128 (fusionada)', 'capa nova encesa · APROXIMACIÓ, no és una cura'),
                                  petit(imC, 'C · quocient B / A', 'isolínies: E; fletxa: zenit; sense color: sense dada')]),
             SORT / NOMS['b04'], icc)

# ------------------------------------------------------------------------------------------------ b05 · el perfil del limbe
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

D = np.load(RES / 'PERFIL_LIMBE_V128B.npz')
rc, r50, E_sec, RL = D['rc'], D['r50'], D['E_sec'], float(D['RL'])
C_NOVA, C_VELLA, C_V125, C_CEL = '#2a78d6', '#eb6834', '#52514e', '#9a9893'
TXT, TXT2, GRAELLA, SUP = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
VZ = np.array(E1['zenit']['vector_imatge_xfila'])
ang_z = np.degrees(np.arctan2(VZ[1], VZ[0])) % 360.0
centres = 10 * np.arange(36) + 5.0


def costat(nom):
    a0 = ang_z if nom == 'zenit' else (ang_z + 180) % 360
    d = np.abs((centres - a0 + 180) % 360 - 180)
    return float(np.median(r50[d <= 15]))


plt.rcParams.update({'font.size': 12, 'axes.edgecolor': TXT2, 'axes.labelcolor': TXT, 'xtick.color': TXT2, 'ytick.color': TXT2,
                     'axes.titlesize': 13, 'axes.titleweight': 'bold', 'axes.titlecolor': TXT})
fig = plt.figure(figsize=(16, 13.5), dpi=150, facecolor=SUP)
gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.15], hspace=0.42, wspace=0.16, left=0.06, right=0.985, top=0.845, bottom=0.075)
v1p = v1b['proves']
fig.text(0.06, 0.968, 'V128 · la capa A arran del limbe: la correcció arriba fins on hi ha dada', fontsize=18, weight='bold', color=TXT)
fig.text(0.06, 0.945, (f'Regla predeclarada: r < {R_INT:g} px, intacte · {R_INT:g}–{R_EXT:g} px, E només on la lluminància passa del cel '
                       f'(Y > cel) · més enllà, E com abans.\nGràfic en lloc de retalls; r = distància al centre de la Lluna de C2 '
                       '(GEOMETRIA_FINAL.json).'), fontsize=12, color=TXT2, va='top')
p6 = v1p['P6_perfil_del_guany']
def mil(n):
    return f'{int(n):,}'.replace(',', '.')


fig.text(0.06, 0.903, (f'Píxels foscos de l\'anell (Y ≤ cel) canviats: {mil(v1p["P3_fosc_intacte"]["anell_fosc_diferents"])} de '
                       f'{mil(v1p["P3_fosc_intacte"]["anell_fosc_n"])}; dels {mil(v1p["P3_fosc_intacte"]["foscos_del_v5"]["n"])} foscos que '
                       f'la V128 anterior corregia, {mil(v1p["P3_fosc_intacte"]["foscos_del_v5"]["canviats_capa_nova"])}.\n'
                       f'Veïns amb corona als dos costats i guany diferent: {mil(p6["parells_capa_nova"]["amb_dada_als_dos_costats"])} '
                       f'(V128 anterior: {mil(p6["parells_capa_anterior"]["amb_dada_als_dos_costats"])}).'),
         fontsize=12, color=TXT, va='top')


def eixos(ax, titol, ylabel):
    ax.set_facecolor(SUP)
    ax.grid(True, color=GRAELLA, lw=0.8)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.set_title(titol, loc='left', pad=8)
    ax.set_ylabel(ylabel)


def marques(ax, rlimbe, text=True):
    ax.axvspan(R_INT, R_EXT, color='#f1efe8', zorder=0)
    ax.axvline(RL, color=C_VELLA, lw=1.2, ls=':', zorder=1)
    ax.axvline(rlimbe, color=TXT2, lw=1.2, ls='--', zorder=1)
    if text:
        tr = ax.get_xaxis_transform()                              # x en px, y en fracció de l'eix
        ax.text(R_INT + 0.4, 0.98, f'anell {R_INT:g}–{R_EXT:g} px', va='top', ha='left', fontsize=10, color=TXT2, transform=tr)
        ax.text(RL + 0.4, 0.55, 'cercle de la\nV128 anterior', va='top', ha='left', fontsize=10, color=C_VELLA, transform=tr)
        ax.text(rlimbe + 0.4, 0.98, f'limbe real ({rlimbe:.1f} px)'.replace('.', ','), va='top', ha='left', fontsize=10,
                color=TXT2, transform=tr)


for col, nom, etq in ((0, 'zenit', 'cap al zenit (±15°)'), (1, 'horitzo', 'cap a l\'horitzó (±15°)')):
    rlim = costat(nom)
    ax = fig.add_subplot(gs[0, col])
    eixos(ax, f'Lluminància lineal, {etq}', 'Y (mediana cada 0,5 px)' if col == 0 else None)
    ax.semilogy(rc, D[f'{nom}_Y'], color=C_V125, lw=2, label='V125-FINAL (entrada)')
    ax.semilogy(rc, D[f'{nom}_Ys'], color=C_CEL, lw=2, ls='--', label='cel ajustat (el llindar)')
    ax.set_xlim(rc[0] - 0.25, rc[-1] + 0.25)
    marques(ax, rlim)
    if col == 0:
        ax.legend(loc='lower right', frameon=False, fontsize=11)
    ax = fig.add_subplot(gs[1, col])
    eixos(ax, f'Quocient V128 / V125, {etq}', 'lluminància: després / abans' if col == 0 else None)
    ax.plot(rc, D[f'{nom}_E'], color=C_CEL, lw=1.5, ls='--', label='E (el guany de la corona)')
    ax.plot(rc, D[f'{nom}_qv'], color=C_VELLA, lw=2, label='V128 anterior (cercle fix)')
    ax.plot(rc, D[f'{nom}_qn'], color=C_NOVA, lw=2, label='V128 nova (regla per dada)')
    ax.axhline(1.0, color=TXT2, lw=0.8)
    ax.set_xlim(rc[0] - 0.25, rc[-1] + 0.25)
    lo, hi = np.nanmin([D[f'{nom}_qv'], D[f'{nom}_qn'], D[f'{nom}_E']]), np.nanmax([D[f'{nom}_qv'], D[f'{nom}_qn'], D[f'{nom}_E']])
    pad = 0.15 * (hi - lo)
    ax.set_ylim(lo - pad, hi + 2.2 * pad)
    marques(ax, rlim)
    ax.set_xlabel('r (px des del centre lunar)')
    if col == 0:
        ax.legend(loc='center left', frameon=False, fontsize=11)
for col, clau, titol, color in ((0, 'sec_fr_v', 'V128 anterior: fracció de la correcció aplicada a la corona', C_VELLA),
                                (1, 'sec_fr_n', 'V128 nova: fracció de la correcció aplicada a la corona', C_NOVA)):
    ax = fig.add_subplot(gs[2, col])
    eixos(ax, titol, '(Ĝ − 1) / (E − 1)  ·  1 = tota, 0 = gens' if col == 0 else None)
    fr = D[clau]
    for s in range(36):
        if np.all(np.isnan(fr[s])):
            continue
        ax.plot(rc - r50[s], fr[s], color=color, lw=1.0, alpha=0.55)
    ax.axhline(1.0, color=TXT2, lw=0.8)
    ax.axhline(0.0, color=TXT2, lw=0.8)
    ax.axvline(0.0, color=TXT2, lw=1.2, ls='--')
    ax.set_ylim(-0.12, 1.18)
    ax.set_xlim(-6, 24)
    ax.set_xlabel('distància al limbe real del sector (px; > 0, fora)')
    ax.text(0.3, 1.13, 'limbe real', fontsize=10, color=TXT2, va='top')
    n_sec = int(np.sum(~np.all(np.isnan(fr), axis=1)))
    ax.text(23.5, 0.08, f'{n_sec} sectors de 10° amb |E − 1| ≥ 0,02;\nnomés píxels amb corona (Y − cel > 0,002)',
            fontsize=10, color=TXT2, ha='right', va='bottom')
fig.text(0.06, 0.012, ('Dades: V125-FINAL (entrada de l\'e3), capa A anterior (OUT_rgb16, SHA 29f783ac…) i capa A nova (OUTB, '
                       f'SHA {v1b["matriu"]["sha256_bytes_OUTB"][:8]}…), iguals a les dels fitxers (v3, v3b).\n'
                       'Ĝ = (Y′ − cel)/(Y − cel): el guany que porta la part de corona. Franja gris: l\'anell on decideix la dada. '
                       'Línia de punts taronja: el cercle on s\'aturava la V128 anterior.'), fontsize=10, color=TXT2)
tmp5 = TREB / 'v4b_05_srgb.png'
fig.savefig(tmp5, dpi=150, facecolor=SUP)
plt.close(fig)
im5 = ed.srgb_a_adobe(Image.open(tmp5), icc)
im5.save(SORT / NOMS['b05'], icc_profile=icc, optimize=True)
print(f'b04 i b05 ({im5.size}) ({time.time() - T0:.0f} s)', flush=True)

# xifres de control de la vista (per al rebut): quocient als sectors de ±15° a 1,5–4 R☉
r, pa = g.polar(XX, YY)
dpa = np.abs((pa - PAZ + 180) % 360 - 180)
sect = {}
for rr in (1.5, 2.0, 3.0, 4.0):
    for nom, m in (('zenit', dpa <= 15), ('horitzo', dpa >= 165)):
        m = m & (np.abs(r - rr) <= 0.1) & ~mask_v
        sect[f'{rr}_{nom}'] = dict(quocient_mitja=float(np.nanmean(quoc[m])), E=float(Ev[m].mean()))
v4 = json.load(open(RES / 'V4_VISTES.json'))
info = dict(guio=str(Path(__file__).resolve().relative_to(ARREL)), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
            fusionada_del_fitxer_igual_a_OUTB=fus_igual_OUTB,
            vistes={n: ed.sha256(SORT / n) for n in NOMS.values()}, mida_px=list(imA.size), mida_px_b05=list(im5.size),
            perfil=ii['desc'], b01_identica_a_la_01_del_v4=ed.sha256(SORT / NOMS['b01']) == v4['vistes'].get('01_V125-FINAL_fusionada.jpg'),
            quocient_sectors_15graus=sect,
            fons_r_mes_6=dict(mediana=float(np.median(quoc[(r > 6) & ~mask_v])), p5=float(np.percentile(quoc[(r > 6) & ~mask_v], 5)),
                              p95=float(np.percentile(quoc[(r > 6) & ~mask_v], 95))),
            segons=round(time.time() - T0, 1))
json.dump(info, open((RES if len(sys.argv) <= 3 else SORT) / 'V4B_VISTES.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(info, indent=1, ensure_ascii=False))

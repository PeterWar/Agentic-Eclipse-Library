"""e2 · PIS 1 (el pis on neix el defecte): el compost lineal fusion_total_v42, sense i amb la correcció de l'extinció diferencial.

Recepta (llum lineal, llenç SENCER de la V42, 10551 × 7506):
  1. F = fusion_total_v42 (cau b3, mmap de NOMÉS LECTURA; SHA de B3_V42_FROZEN), dada = suport ∧ finit ∧ F > 0 als tres canals.
  2. Mitjana per blocs de 3 × 3 píxels amb dada (3517 × 2502): només per fer la vista; E és suau (varia ≤ 0,02 % en 3 px).
  3. Cel: el pla per canal de la v2 (CEL_CANALS_v2.json, r ≥ 8 R☉; el verd és el b_new de CEL_v2.json), passat a l'espai del
     compost amb la inversa exacta de la matriu de color. El cel és llum de l'atmosfera: NO es corregeix.
  4. Corona = F − cel. Corregit = cel + E·(F − cel), amb E = 10^(0,4·0,40·(X − X☉)), X per píxel (msb_comu, graella d'astropy
     al llenç V42, 18:29:34 UT) i X☉ = 6,053. El mateix E als tres canals (acromàtic).
  5. Vista (la MATEIXA als dos panells): verd natiu de la càmera de la corona, D = (corona + c)/(P(r) + c), amb P(r) el perfil
     radial (mediana per anell) de la corona SENSE corregir i c = 5 ADU/s (C_SUAU); gris = (log10 D − LO)/(HI − LO). Res més.
Escriu a Sortides/extincio_diferencial_20261012/ les vistes P1_* i a resultats/… E2_PIS1.json (perfil, balanç per canal, proves)."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np                                                 # noqa: E402
from PIL import Image                                              # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ed_comu as ed            # noqa: E402

mc = ed.mc
T0 = time.time()
S = 3                                     # blocs de 3 × 3
C_SUAU = 5.0                             # ADU/s (verd de la càmera): suavitza la divisió on la corona < cel
LO, HI = -0.40, 0.40                      # log10 D: límits fixos de la vista (iguals als dos panells)
AMPLE = 3000                              # px de les vistes soles
ed.SORT.mkdir(parents=True, exist_ok=True)
ed.RES.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------------------------ 1–2. compost per blocs
cau = mc.obre_cau()
Fm = cau['fusion_total_v42']
sup_m = np.load(mc.troba_cau() / 'support_v42.npy', mmap_mode='r')
H, W = mc.H, mc.W
assert Fm.shape == (H, W, 3) and H % S == 0 and W % S == 0
hb, wb = H // S, W // S
suma = np.zeros((hb, wb, 3), np.float64)
n = np.zeros((hb, wb), np.int32)
PAS = 600
for y0 in range(0, H, PAS):
    y1 = min(H, y0 + PAS)
    F = np.asarray(Fm[y0:y1], np.float64)
    d = np.asarray(sup_m[y0:y1]) & np.all(np.isfinite(F), 2) & np.all(F > 0, 2)
    F[~d] = 0.0
    hh = (y1 - y0) // S
    suma[y0 // S:y0 // S + hh] = F.reshape(hh, S, wb, S, 3).sum(axis=(1, 3))
    n[y0 // S:y0 // S + hh] = d.reshape(hh, S, wb, S).sum(axis=(1, 3))
del F, d
dada = n > 0
Fb = np.where(dada[..., None], suma / np.maximum(n, 1)[..., None], np.nan)
del suma
print(f'blocs {Fb.shape}, amb dada {dada.mean():.3f} ({time.time() - T0:.0f} s)', flush=True)

# coordenades del centre de cada bloc al llenç V42
yc = np.arange(hb) * S + (S - 1) / 2.0
xc = np.arange(wb) * S + (S - 1) / 2.0
XX, YY = np.meshgrid(xc, yc)
g = mc.geo_llenc()
r, pa = g.polar(XX, YY)

# ------------------------------------------------------------------------------------------------ 3–4. cel, E, correcció
cel = ed.cel_F_v42(XX, YY)                                         # (hb, wb, 3)
sp = ed.Spline(ed.GRAELLA_V42)
X = sp.X_graella(yc, xc)
E = ed.factor_E(X, sp.X_sol)
cor = Fb - cel                                                     # corona (llum de damunt l'atmosfera, atenuada)
Fc = cel + E[..., None] * cor                                      # corregit
A = mc.matriu_inversa()
Gnet = np.einsum('j,...j->...', A[1], cor)                         # verd natiu de la càmera, corona
Gnet_c = E * Gnet
print(f'E {np.nanmin(E):.3f}–{np.nanmax(E):.3f}; X☉ {sp.X_sol:.4f} ({time.time() - T0:.0f} s)', flush=True)

# ------------------------------------------------------------------------------------------------ 5. perfil i vista
rm = np.hypot(XX - mc.LLUNA_XY[0], YY - mc.LLUNA_XY[1])
ghost = np.hypot(XX - mc.GHOST_XY[0], YY - mc.GHOST_XY[1]) < mc.GHOST_R_PX
ok_perfil = dada & (n == S * S) & (rm >= mc.R_BANDA_PX) & ~ghost & np.isfinite(Gnet)
vores = np.r_[np.linspace(1.0, 2.0, 51), np.linspace(2.0, 13.0, 221)[1:]]
rc = 0.5 * (vores[1:] + vores[:-1])
idx = np.digitize(r[ok_perfil], vores) - 1
vals = Gnet[ok_perfil]
med = np.full(len(rc), np.nan)
npix = np.zeros(len(rc), int)
for i in range(len(rc)):
    s = vals[idx == i]
    npix[i] = s.size
    if s.size >= 200:
        med[i] = np.median(s)
bo = np.isfinite(med)
# mitjana corrent de 5 anells (mediana) per treure soroll del perfil
med_s = med.copy()
for i in np.where(bo)[0]:
    w = med[max(0, i - 2):i + 3]
    med_s[i] = np.nanmedian(w)
# Més enllà del cercle inscrit (~8,5 R☉) l'anell ja no és complet i la mediana salta (bony de 4,8 a 6,4 ADU/s a 8,5–9 R☉):
# es força el perfil a no créixer cap enfora (mínim acumulat). Només toca la vista, i igual als dos panells.
med_m = med_s.copy()
med_m[bo] = np.minimum.accumulate(med_s[bo])
P = np.interp(r, rc[bo], med_m[bo], left=med_m[bo][0], right=med_m[bo][-1])


def vista(gn):
    D = (gn + C_SUAU) / (np.maximum(P, 0.0) + C_SUAU)
    with np.errstate(invalid='ignore', divide='ignore'):
        L = np.log10(np.where(D > 0, D, np.nan))
    v = (L - LO) / (HI - LO)
    v = np.where(np.isfinite(L), np.clip(v, 0, 1), 0.0)            # corona ≤ −c (soroll sota el cel): negre
    return v


SENSE = (0.13, 0.15, 0.22)                                         # color de «sense dada» (blau pissarra fosc)


def a_rgb(v, ample):
    vv = ed.redueix_float(v, ample)
    mm = ed.redueix_float(dada.astype(np.float32), ample) > 0.5
    out = np.empty(vv.shape + (3,), np.float32)
    for k in range(3):
        out[..., k] = np.where(mm, np.clip(vv, 0, 1), SENSE[k])
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8))


vA, vB = vista(Gnet), vista(Gnet_c)
from psd_tools import PSDImage                                     # noqa: E402
from psd_tools.constants import Resource                          # noqa: E402
icc = PSDImage.open(ed.PSB).image_resources.get_data(Resource.ICC_PROFILE)   # perfil Adobe RGB (1998) de la final, NOMÉS LECTURA

titA = 'PIS 1 · compost lineal · SENSE corregir l\'extinció diferencial'
titB = 'PIS 1 · compost lineal · AMB la correcció E (acromàtica, només a la llum de la corona)'
sub = ('Corona sense el cel, verd de la càmera, dividida pel MATEIX perfil radial als dos panells; escala logarítmica fixa. '
       'Llenç sencer. Blau fosc: sense dada.')
imA = a_rgb(vA, AMPLE)
imB = a_rgb(vB, AMPLE)
ed.desa_jpeg(ed.amb_rotol(imA, titA, sub), ed.SORT / 'P1_A_compost_lineal_sense_correccio.jpg', icc)
ed.desa_jpeg(ed.amb_rotol(imB, titB, sub), ed.SORT / 'P1_B_compost_lineal_amb_correccio.jpg', icc)
print(f'vistes A i B ({time.time() - T0:.0f} s)', flush=True)

# ------------------------------------------------------------------------------------------------ panell C: E amb isolínies i zenit
E1 = json.load(open(ed.RES / 'E1_MASSA_AIRE_FINAL.json'))
PAZ = E1['zenit']['PA_solar_deg']['r1']





esc_vista = W / AMPLE                      # px del llenç per px de la vista
fonsC = ed.redueix_float(vA, AMPLE)
Ev = ed.redueix_float(E.astype(np.float32), AMPLE)
geoV = mc.Geo(g.cx, g.cy, g.R, g.n, g.e)
tmp = ed.RES / '_P1_C_srgb.png'
ed.panell_factor(fonsC, Ev, Ev, geoV, esc_vista, PAZ, tmp, ample=AMPLE, etiqueta='E (factor de correcció)')
imC = ed.srgb_a_adobe(Image.open(tmp), icc)
imC = imC.resize((imA.width, imA.height), Image.LANCZOS) if imC.size != imA.size else imC
titC = 'PIS 1 · factor E = 10^(0,4·0,40·(X − X☉)) per píxel, a les 18:29:34 UT'
subC = (f'E < 1 cap al zenit (PA solar {PAZ:.1f}°, fletxa groga), E > 1 cap a l\'horitzó. '.replace(f'{PAZ:.1f}', f'{PAZ:.1f}'.replace('.', ',')) +
        'Cercles: limbe, 1,5 i 4 R☉. A sota, la vista A en gris. Escala de color saturada a 0,7 i 1,43.')
ed.desa_jpeg(ed.amb_rotol(imC, titC, subC), ed.SORT / 'P1_C_factor_E.jpg', icc)
tmp.unlink()

# costat a costat (1500 px per panell)
mig = AMPLE // 2
pA = ed.amb_rotol(imA.resize((mig, int(round(imA.height * mig / imA.width))), Image.LANCZOS), 'A · sense corregir',
                  'compost lineal, mateixa vista')
pB = ed.amb_rotol(imB.resize((mig, int(round(imB.height * mig / imB.width))), Image.LANCZOS), 'B · amb la correcció E',
                  'compost lineal, mateixa vista')
pC = ed.amb_rotol(imC.resize((mig, int(round(imC.height * mig / imC.width))), Image.LANCZOS), 'C · factor E',
                  'zenit: fletxa groga')
ed.desa_jpeg(ed.costat_a_costat([pA, pB, pC]), ed.SORT / 'P1_costat_a_costat.jpg', icc)
print(f'panell C i costat a costat ({time.time() - T0:.0f} s)', flush=True)

# ------------------------------------------------------------------------------------------------ proves i balanç per canal
anells = [(1.1, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.5)]
dz = np.cos(np.radians(pa - PAZ))                                  # > 0: meitat del zenit
ok = dada & (n == S * S) & (rm >= mc.R_BANDA_PX) & ~ghost & np.all(np.isfinite(Fb), 2)
bal = []
for a, b in anells:
    for nom_m, m in (('anell', (r >= a) & (r < b)), ('meitat_zenit', (r >= a) & (r < b) & (dz > 0)),
                     ('meitat_horitzo', (r >= a) & (r < b) & (dz < 0))):
        m = m & ok
        fila = dict(r=[a, b], zona=nom_m, n_blocs=int(m.sum()), E_mitjana=float(E[m].mean()))
        for etq, arr in (('total_abans', Fb), ('total_despres', Fc), ('corona_abans', cor), ('corona_despres', E[..., None] * cor)):
            mu = arr[m].mean(0)
            fila[etq] = dict(R_G=float(mu[0] / mu[1]), B_G=float(mu[2] / mu[1]))
        bal.append(fila)
# per píxel: R/G i B/G de la corona no canvien (acromàtic)
mk = ok & (np.abs(cor[..., 1]) > 1.0)
dRG = np.abs((E[..., None] * cor)[..., 0][mk] / (E * cor[..., 1])[mk] - cor[..., 0][mk] / cor[..., 1][mk])
# res més canvia: on E = 1 la diferència és zero; el cel és idèntic
quasi1 = ok & (np.abs(E - 1) < 1e-4)
dif_E1 = float(np.nanmax(np.abs(Fc[quasi1] - Fb[quasi1]) / np.maximum(np.abs(Fb[quasi1]), 1e-9))) if quasi1.any() else None
# control nul: amb E ≡ 1, el corregit és el compost (fins a l'arrodoniment)
nul = float(np.nanmax(np.abs((cel + 1.0 * cor) - Fb)))
# dipol de la vista: ln(corregit/sense) en funció de la direcció (ha de seguir el zenit)
mm = ok & (r > 1.2) & (r < 5.5) & (Gnet > 50)
lnq = np.log(Gnet_c[mm] / Gnet[mm])
ab = np.c_[np.ones(mm.sum()), np.cos(np.radians(pa[mm])) * r[mm], np.sin(np.radians(pa[mm])) * r[mm]]
cf, *_ = np.linalg.lstsq(ab, lnq, rcond=None)
pa_dip = math.degrees(math.atan2(cf[2], cf[1])) % 360

perfil = [dict(r=float(rc[i]), n=int(npix[i]), mediana=float(med[i]) if bo[i] else None,
               suau=float(med_s[i]) if bo[i] else None, vista=float(med_m[i]) if bo[i] else None) for i in range(len(rc))]
out = dict(
    guio=ed.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    entrada=dict(cau=ed.rel(mc.troba_cau()), sha256_esperat={k: mc.SHA_CAU[k] for k in ('fusion_total_v42.npy', 'support_v42.npy')},
                 cel=ed.rel(ed.CEL_CANALS), massa_aire=ed.rel(ed.GRAELLA_V42)),
    recepta=dict(blocs=S, k=ed.K, X_sol=sp.X_sol, E='10^(0,4·k·(X − X☉))', ordre='primer el cel (no es corregeix), després E',
                 vista=dict(D='(corona_G + c)/(P(r) + c)', c_ADU_s=C_SUAU, log10_lo=LO, log10_hi=HI,
                            P='mediana per anell de la corona SENSE corregir (fora de la franja lunar i del fantasma), '
                              'mediana corrent de 5 anells, forçada a no créixer cap enfora (mínim acumulat)',
                            mateixa_als_dos_panells=True),
                 llenc=[W, H], vista_px=[imA.width, imA.height]),
    E_min_max_llenc=[float(np.nanmin(E)), float(np.nanmax(E))],
    proves=dict(
        RG_per_pixel_corona_max_abs_dif=float(dRG.max()), n_pixels=int(mk.sum()),
        dif_relativa_max_on_E_1=dif_E1, n_blocs_E_1=int(quasi1.sum()),
        control_nul_E_igual_1_max_abs=nul,
        direccio_on_creix_la_correccio_PA_deg=pa_dip, horitzo_PA_deg=(PAZ + 180.0) % 360,
        angle_vs_horitzo_deg=abs((pa_dip - PAZ - 180.0 + 180) % 360 - 180)),
    balanc_per_canal=bal, perfil_radial_G_ADU_s=perfil, segons=round(time.time() - T0, 1))
ed.json_dump(out, ed.RES / 'E2_PIS1.json')
for f in bal:
    if f['zona'] == 'anell':
        print(f"{f['r']} E̅ {f['E_mitjana']:.3f} total R/G {f['total_abans']['R_G']:.4f}→{f['total_despres']['R_G']:.4f} "
              f"B/G {f['total_abans']['B_G']:.4f}→{f['total_despres']['B_G']:.4f} | corona R/G {f['corona_abans']['R_G']:.4f}→"
              f"{f['corona_despres']['R_G']:.4f}")
print(f"proves: R/G per píxel {dRG.max():.1e}; on E=1 {dif_E1}; nul {nul:.1e}; direcció del canvi PA {pa_dip:.1f}° (zenit {PAZ}°)")
print(f'fet ({time.time() - T0:.0f} s)')

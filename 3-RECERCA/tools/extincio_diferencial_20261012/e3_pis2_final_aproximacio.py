"""e3 · PIS 2 (APROXIMACIÓ VISUAL, no és una cura): la imatge fusionada de la V125-FINAL amb la correcció de l'extinció.

Per què és només una aproximació: la final no és llum lineal. Porta corbes, filtres i les capes de Pere. Desfer la corba del
perfil (Adobe RGB, potència 563/256) no la torna proporcional a la llum. Una cura de debò es fa al compost lineal (pis 1) i es
refà tot el que hi ha a sobre, capes de Pere incloses.

Recepta (llenç SENCER de la final, 7933 × 5021, a resolució plena):
  1. La imatge fusionada de la V125-FINAL.psb (psd-tools, NOMÉS LECTURA; mai el Photoshop). Es comprova el SHA-256 del PSB.
  2. Adobe RGB lineal: lin = (valor/65535)^(563/256), la corba del perfil incrustat (es llegeix i es comprova).
  3. El cel de la final (PREDECLARAT abans de mirar el resultat): per canal, polinomi de grau 2 en (u, v) = (x − x☉, fila − y☉)/R☉
     ajustat a la mitjana per blocs de 8 × 8 px a r ≥ 6 R☉, sense estrelles (residu de la mediana 7 × 7 > 5σ, eixamplat 2 blocs),
     6 rondes de retall asimètric (+2,5σ / −4σ: la corona només suma). El cel NO es toca.
     (La màscara d'estrelles només es busca a r > 3 R☉: més endins, el residu de la mediana és estructura de corona.)
  4. E del marc de la final (e1: geometria pròpia, GEOMETRIA_FINAL.json; graella d'astropy). El mateix E a R, G i B.
  5. lin' = cel + E·(lin − cel) fora del disc lunar. El disc lunar (la Lluna de C2 de Pere, R 453,6 px) queda IDÈNTIC: allà la
     final és més fosca que el cel i (lin − cel) no és llum de corona.
  6. Es torna a codificar amb el mateix perfil: valor = clip(lin', 0, 1)^(256/563), 16 bits. Es compten els píxels retallats.
Proves: control nul (E ≡ 1 ⇒ els 16 bits idèntics), disc lunar idèntic, diferència on E = 1, R/G i B/G de la corona per píxel,
balanç per canal en anells i meitats (zenit / horitzó), direcció del canvi contra el zenit.
Escriu les vistes P2_* a Sortides/extincio_diferencial_20261012/ i E3_PIS2.json a resultats/."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ed_comu as ed            # noqa: E402

mc = ed.mc
T0 = time.time()
AMPLE = 3000
SB = 8                                   # blocs per al cel
R_CEL = 6.0                              # R☉: el cel s'ajusta a r ≥ R_CEL
GRAU = 2
RETALL = (2.5, 4.0)                      # +σ, −σ
RONDES = 6

# ------------------------------------------------------------------------------------------------ 1. la final
sha_psb = ed.sha256(ed.PSB)
if sha_psb != ed.SHA_PSB_ESTAT:
    print(f'⚠️ El SHA del PSB no és el d\'ESTAT.md: {sha_psb}', flush=True)
U, icc = ed.llegeix_final()
ii = ed.info_icc(icc)
if not (ii['desc'] == 'Adobe RGB (1998)' and all(abs(ii[c] - ed.GAMMA) < 1e-9 for c in ('rTRC', 'gTRC', 'bTRC'))):
    raise SystemExit(f'El perfil de la final no és Adobe RGB (1998) amb γ 563/256: {ii}')
YC = np.array(ii['Y'])
H, W = ed.HF, ed.WF
print(f'final {U.shape} llegida, SHA {sha_psb[:12]}…, perfil {ii["desc"]} ({time.time() - T0:.0f} s)', flush=True)

g = ed.geo_final()
sp = ed.Spline(ed.GRAELLA_FINAL)
E1 = json.load(open(ed.RES / 'E1_MASSA_AIRE_FINAL.json'))
PAZ = E1['zenit']['PA_solar_deg']['r1']

# ------------------------------------------------------------------------------------------------ 3. el cel de la final
hb, wb = H // SB, W // SB
lin_b = ((U[:hb * SB, :wb * SB].astype(np.float64) / 65535.0) ** ed.GAMMA).reshape(hb, SB, wb, SB, 3).mean(axis=(1, 3))
ycb = np.arange(hb) * SB + (SB - 1) / 2.0
xcb = np.arange(wb) * SB + (SB - 1) / 2.0
XB, YB = np.meshgrid(xcb, ycb)
rb, pab = g.polar(XB, YB)
Yb = lin_b @ YC
res = Yb - nd.median_filter(Yb, size=7)
zs = rb > 4.0
sd = 1.4826 * np.median(np.abs(res[zs] - np.median(res[zs])))
estrelles = nd.binary_dilation((res > 5 * sd) & (rb > 3.0), iterations=2)   # a dins de 3 R☉ el residu és estructura de corona
sel = (rb >= R_CEL) & ~estrelles


def termes(x, y):
    u, v = (np.asarray(x, np.float64) - g.cx) / g.R, (np.asarray(y, np.float64) - g.cy) / g.R
    t = [np.ones_like(u), u, v]
    if GRAU >= 2:
        t += [u * u, u * v, v * v]
    return t


TB = termes(XB, YB)
Am = np.stack([t[sel] for t in TB], 1)
coef, info_cel = [], []
for c in range(3):
    y = lin_b[..., c][sel]
    w = np.ones(len(y), bool)
    for _ in range(RONDES):
        cf, *_ = np.linalg.lstsq(Am[w], y[w], rcond=None)
        rr = y - Am @ cf
        md = np.median(rr[w]); s = 1.4826 * np.median(np.abs(rr[w] - md))
        w = (rr - md < RETALL[0] * s) & (rr - md > -RETALL[1] * s)
    coef.append(cf)
    info_cel.append(dict(canal='RGB'[c], coef=cf.tolist(), n=int(len(y)), n_final=int(w.sum()), sigma=float(s)))
coef = np.array(coef)                                    # (3, nterms)


def cel(x, y):
    t = termes(x, y)
    return np.stack([sum(coef[c, i] * t[i] for i in range(len(t))) for c in range(3)], axis=-1)


celb = cel(XB, YB)
qcel = (lin_b[..., 1] - celb[..., 1]) / celb[..., 1]
cel_resid = {}
for a, b in ((4, 5), (5, 6), (6, 7), (7, 8), (8, 11)):
    m = (rb >= a) & (rb < b) & ~estrelles
    cel_resid[f'{a}-{b}'] = float(np.median(qcel[m]))
for nom, m in (('dalt_centre', (YB < 300) & (np.abs(XB - g.cx) < 600)), ('baix_centre', (YB > H - 300) & (np.abs(XB - g.cx) < 600))):
    cel_resid[nom] = float(np.median(qcel[m & ~estrelles]))
print(f'cel: {info_cel[1]["coef"]} | residu mediana (lin−cel)/cel: {cel_resid} ({time.time() - T0:.0f} s)', flush=True)

# ------------------------------------------------------------------------------------------------ 4–6. correcció a resolució plena
OUT = np.empty_like(U)
retall_alt = retall_baix = 0
nul_dif = 0
lluna_dif = 0
max_dif_E1 = 0
n_E1 = 0
max_dRG = max_dBG = 0.0
PAS = 512
cols = np.arange(W, dtype=np.float64)
for y0 in range(0, H, PAS):
    y1 = min(H, y0 + PAS)
    rows = np.arange(y0, y1, dtype=np.float64)
    XX, YY = np.meshgrid(cols, rows)
    u0 = U[y0:y1]
    lin = (u0.astype(np.float64) / 65535.0) ** ed.GAMMA
    S = cel(XX, YY)
    E = ed.factor_E(sp.X_graella(rows, cols), sp.X_sol)
    lluna = np.hypot(XX - ed.LLUNA_F[0], YY - ed.LLUNA_F[1]) <= ed.R_LLUNA_F
    Ee = np.where(lluna, 1.0, E)
    cor = lin - S
    lin2 = S + Ee[..., None] * cor
    retall_alt += int(np.any(lin2 > 1.0, axis=2).sum())
    retall_baix += int(np.any(lin2 < 0.0, axis=2).sum())
    o = np.round(np.clip(lin2, 0.0, 1.0) ** (1.0 / ed.GAMMA) * 65535.0).astype(np.uint16)
    OUT[y0:y1] = o
    # control nul: el mateix camí amb E ≡ 1
    on = np.round(np.clip(S + cor, 0.0, 1.0) ** (1.0 / ed.GAMMA) * 65535.0).astype(np.uint16)
    nul_dif += int(np.any(on != u0, axis=2).sum())
    lluna_dif += int(np.any((o != u0) & lluna[..., None], axis=2).sum())
    q1 = (np.abs(E - 1.0) < 1e-4) & ~lluna
    if q1.any():
        n_E1 += int(q1.sum())
        max_dif_E1 = max(max_dif_E1, int(np.abs(o.astype(np.int32) - u0.astype(np.int32))[q1].max()))
    # R/G i B/G de la corona, per píxel (fora del disc, sense retall, corona clara)
    ok = ~lluna & np.all((lin2 <= 1.0) & (lin2 >= 0.0), axis=2) & (cor[..., 1] > 0.01)
    if ok.any():
        c2 = Ee[..., None] * cor
        max_dRG = max(max_dRG, float(np.max(np.abs(c2[..., 0][ok] / c2[..., 1][ok] - cor[..., 0][ok] / cor[..., 1][ok]))))
        max_dBG = max(max_dBG, float(np.max(np.abs(c2[..., 2][ok] / c2[..., 1][ok] - cor[..., 2][ok] / cor[..., 1][ok]))))
print(f'corregida: retallats amunt {retall_alt}, avall {retall_baix}; nul {nul_dif}; lluna {lluna_dif}; on E=1 màx {max_dif_E1} DN '
      f'({n_E1} px); ΔR/G {max_dRG:.1e} ΔB/G {max_dBG:.1e} ({time.time() - T0:.0f} s)', flush=True)

# ------------------------------------------------------------------------------------------------ balanç per canal (blocs de 8)
lin_a = lin_b
lin_d = ((OUT[:hb * SB, :wb * SB].astype(np.float64) / 65535.0) ** ed.GAMMA).reshape(hb, SB, wb, SB, 3).mean(axis=(1, 3))
enc_a = (U[:hb * SB, :wb * SB].astype(np.float64) / 65535.0).reshape(hb, SB, wb, SB, 3).mean(axis=(1, 3))
enc_d = (OUT[:hb * SB, :wb * SB].astype(np.float64) / 65535.0).reshape(hb, SB, wb, SB, 3).mean(axis=(1, 3))
rmb = np.hypot(XB - ed.LLUNA_F[0], YB - ed.LLUNA_F[1])
Eb = ed.factor_E(sp.X_graella(ycb, xcb), sp.X_sol)
dz = np.cos(np.radians(pab - PAZ))
okb = rmb >= mc.R_BANDA_PX            # fora de la franja lunar (la màscara d'estrelles s'emporta raigs: aquí no s'aplica)
bal = []
for a, b in ((1.1, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.5)):
    for zona, m in (('anell', (rb >= a) & (rb < b)), ('meitat_zenit', (rb >= a) & (rb < b) & (dz > 0)),
                    ('meitat_horitzo', (rb >= a) & (rb < b) & (dz < 0))):
        m = m & okb
        f = dict(r=[a, b], zona=zona, n_blocs=int(m.sum()), E_mitjana=float(Eb[m].mean()))
        for etq, arr in (('lineal_abans', lin_a), ('lineal_despres', lin_d), ('corona_abans', lin_a - celb),
                         ('corona_despres', lin_d - celb), ('codificat_abans', enc_a), ('codificat_despres', enc_d)):
            mu = arr[m].mean(0)
            f[etq] = dict(R_G=float(mu[0] / mu[1]), B_G=float(mu[2] / mu[1]))
        f['lluminancia_lineal_despres_sobre_abans'] = float((lin_d[m] @ YC).mean() / (lin_a[m] @ YC).mean())
        bal.append(f)

# quocient de lluminància lineal (després / abans), per blocs
Ya, Yd = lin_a @ YC, lin_d @ YC
quoc = Yd / Ya
# E recuperat del fitxer de sortida: Ê = (Y_després − Y_cel)/(Y_abans − Y_cel), on la corona fa més de la meitat de la llum.
# Ha de ser E (mateixa direcció i mateix valor): prova que el guany que porta la imatge nova és el de la massa d'aire, ben posat.
Ycel = celb @ YC
fY = (Ya - Ycel) / Ya
mm = okb & (rb > 1.2) & (rb < 5.5) & (fY > 0.5)
Erec = (Yd[mm] - Ycel[mm]) / (Ya[mm] - Ycel[mm])
ab = np.c_[np.ones(mm.sum()), (XB[mm] - g.cx) / g.R, (YB[mm] - g.cy) / g.R]
cf, *_ = np.linalg.lstsq(ab, np.log(Erec), rcond=None)
vimg = np.array([cf[1], cf[2]]); vimg /= np.linalg.norm(vimg)
vz = np.array(E1['zenit']['vector_imatge_xfila'])
ang_horitzo = math.degrees(math.acos(float(np.clip(vimg @ (-vz), -1, 1))))
dErec = Erec / Eb[mm] - 1
print(f'E recuperat: direcció a {ang_horitzo:.2f}° de l\'horitzó; Ê/E − 1 mediana {np.median(dErec):+.1e}, '
      f'p99 |·| {np.percentile(np.abs(dErec), 99):.1e} (n {mm.sum()}) ({time.time() - T0:.0f} s)', flush=True)

# el fons (r > 6 R☉) no ha de canviar: quocient per zones
fons_q = {}
for nom, m in (('dalt', YB < 0.15 * H), ('baix', YB > 0.85 * H), ('esquerra', XB < 0.08 * W), ('dreta', XB > 0.92 * W)):
    m = m & (rb > 6.0)
    fons_q[nom] = dict(n=int(m.sum()), mediana=float(np.median(quoc[m])), p5=float(np.percentile(quoc[m], 5)),
                       p95=float(np.percentile(quoc[m], 95)))
# canvi visible: sectors de ±15° cap al zenit i cap a l'horitzó
canvi = []
dpa = np.abs((pab - PAZ + 180) % 360 - 180)
for rr in (1.5, 2.0, 3.0, 4.0):
    f = dict(r=rr)
    for nom, m in (('zenit', dpa <= 15), ('horitzo', dpa >= 165)):
        m = m & (np.abs(rb - rr) <= 0.1) & okb
        f[nom] = dict(n_blocs=int(m.sum()), E=float(Eb[m].mean()),
                      lluminancia_lineal_canvi_pc=float(100 * (Yd[m].mean() / Ya[m].mean() - 1)),
                      fraccio_corona=float(np.median(1 - Ycel[m] / Ya[m])),
                      G_codificat_abans_8bits=float(255 * enc_a[m][:, 1].mean()),
                      G_codificat_despres_8bits=float(255 * enc_d[m][:, 1].mean()))
    canvi.append(f)
    print(f"r {rr}: zenit {f['zenit']['lluminancia_lineal_canvi_pc']:+.1f} % ({f['zenit']['G_codificat_abans_8bits']:.0f}→"
          f"{f['zenit']['G_codificat_despres_8bits']:.0f}) | horitzó {f['horitzo']['lluminancia_lineal_canvi_pc']:+.1f} % "
          f"({f['horitzo']['G_codificat_abans_8bits']:.0f}→{f['horitzo']['G_codificat_despres_8bits']:.0f})", flush=True)
print('fons', {k: round(v['mediana'], 4) for k, v in fons_q.items()}, flush=True)


# ------------------------------------------------------------------------------------------------ vistes
def vista_rgb(arr16, ample):
    chans = [ed.redueix_float(arr16[..., c].astype(np.float32) / 65535.0, ample) for c in range(3)]
    return Image.fromarray((np.clip(np.stack(chans, -1), 0, 1) * 255 + 0.5).astype(np.uint8))


imA = vista_rgb(U, AMPLE)
imB = vista_rgb(OUT, AMPLE)
titA = 'PIS 2 · APROXIMACIÓ VISUAL · la final (V125-FINAL) tal com és'
titB = 'PIS 2 · APROXIMACIÓ VISUAL · la final amb la llum de la corona multiplicada per E'
subA = 'Imatge fusionada de la V125-FINAL.psb, llegida sense obrir el Photoshop. Adobe RGB. Llenç sencer.'
subB = ('Mateix guany a R, G i B (el to de la corona no canvia); el cel de la final i el disc lunar, intactes. '
        'No és una cura: una cura es faria al compost lineal i es refaria tot.')
ed.desa_jpeg(ed.amb_rotol(imA, titA, subA, destacat=(255, 200, 80)), ed.SORT / 'P2_A_final_tal_com_es.jpg', icc)
ed.desa_jpeg(ed.amb_rotol(imB, titB, subB, destacat=(255, 200, 80)), ed.SORT / 'P2_B_final_amb_correccio_APROXIMACIO.jpg', icc)

fons = 0.75 * ed.redueix_float((Ya ** (1 / ed.GAMMA)).astype(np.float32), AMPLE)   # una mica enfosquit perquè es vegi el color
qv = ed.redueix_float(quoc.astype(np.float32), AMPLE)
Ev = ed.redueix_float(Eb.astype(np.float32), AMPLE)
lmask = ed.redueix_float((rmb <= ed.R_LLUNA_F).astype(np.float32), AMPLE) > 0.5
qv = np.where(lmask, np.nan, qv)
geoV = mc.Geo(g.cx, g.cy, g.R, g.n, g.e)
tmp = ed.RES / '_P2_C_srgb.png'
ed.panell_factor(fons, qv, Ev, geoV, (wb * SB) / AMPLE, PAZ, tmp,
                 ample=AMPLE, etiqueta='lluminància lineal: després / abans', r_fletxa=4.5, r_text=5.05)
imC = ed.srgb_a_adobe(Image.open(tmp), icc)
if imC.size != imA.size:
    imC = imC.resize(imA.size, Image.LANCZOS)
titC = 'PIS 2 · APROXIMACIÓ VISUAL · quocient després / abans (lluminància lineal)'
subC = (f'Isolínies: E. Zenit a PA solar {PAZ:.1f}° (fletxa groga). '.replace(f'{PAZ:.1f}', f'{PAZ:.1f}'.replace('.', ',')) +
        'On domina la corona, el quocient val E; on domina el cel, 1. Disc lunar: sense color (no es toca).')
ed.desa_jpeg(ed.amb_rotol(imC, titC, subC, destacat=(255, 200, 80)), ed.SORT / 'P2_C_quocient.jpg', icc)
tmp.unlink()
mig = AMPLE // 2


def petit(im, t, s):
    return ed.amb_rotol(im.resize((mig, int(round(im.height * mig / im.width))), Image.LANCZOS), t, s, destacat=(255, 200, 80))


ed.desa_jpeg(ed.costat_a_costat([petit(imA, 'A · la final tal com és', 'APROXIMACIÓ VISUAL'),
                                  petit(imB, 'B · amb la corona × E', 'APROXIMACIÓ VISUAL, no és una cura'),
                                  petit(imC, 'C · quocient B / A', 'isolínies: E; fletxa: zenit')]),
             ed.SORT / 'P2_costat_a_costat.jpg', icc)
print(f'vistes ({time.time() - T0:.0f} s)', flush=True)

out = dict(
    guio=ed.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    entrada=dict(psb=ed.rel(ed.PSB), sha256=sha_psb, sha_igual_a_ESTAT=sha_psb == ed.SHA_PSB_ESTAT,
                 imatge='seccio «Image Data» (la imatge fusionada), psd-tools PSDImage.numpy(); sense compondre capes',
                 perfil=ii, geometria=ed.rel(ed.GEOF), massa_aire=ed.rel(ed.GRAELLA_FINAL)),
    recepta=dict(k=ed.K, X_sol=sp.X_sol, E='10^(0,4·k·(X − X☉))', lineal='(valor/65535)^(563/256)',
                 cel=dict(model=f'polinomi de grau {GRAU} en (u, v) per canal', blocs=SB, r_min_Rsol=R_CEL, retall_sigma=RETALL,
                          rondes=RONDES, estrelles='residu de la mediana 7×7 > 5σ a r > 3 R☉, eixamplat 2 blocs', canals=info_cel,
                          residu_mediana_lin_menys_cel_sobre_cel_G=cel_resid),
                 correccio='lin\' = cel + E·(lin − cel) fora del disc lunar; disc lunar idèntic', codificacio='clip(lin\', 0, 1)^(256/563), 16 bits'),
    proves=dict(control_nul_E_1_pixels_diferents=nul_dif, disc_lunar_pixels_diferents=lluna_dif,
                on_E_1=dict(criteri='|E − 1| < 1e-4', n_px=n_E1, max_dif_DN_16bits=max_dif_E1),
                retallats=dict(per_sobre_de_1=retall_alt, per_sota_de_0=retall_baix, fraccio=(retall_alt + retall_baix) / (H * W)),
                RG_corona_per_pixel_max_abs_dif=max_dRG, BG_corona_per_pixel_max_abs_dif=max_dBG,
                E_recuperat_del_fitxer=dict(criteri='corona > 50 % de la llum, 1,2–5,5 R☉, fora de la franja lunar, blocs de 8',
                                            n_blocs=int(mm.sum()), direccio_graus_de_l_horitzo=ang_horitzo,
                                            mediana_E_rec_sobre_E_menys_1=float(np.median(dErec)),
                                            p99_abs=float(np.percentile(np.abs(dErec), 99)))),
    fons_r_mes_6_quocient=fons_q, canvi_visible_sectors_15graus=canvi,
    balanc_per_canal=bal, vistes_px=[imA.width, imA.height], segons=round(time.time() - T0, 1))
ed.json_dump(out, ed.RES / 'E3_PIS2.json')
for f in bal:
    if f['zona'] != 'anell':
        continue
    print(f"{f['r']} E̅ {f['E_mitjana']:.3f} lin R/G {f['lineal_abans']['R_G']:.4f}→{f['lineal_despres']['R_G']:.4f} "
          f"B/G {f['lineal_abans']['B_G']:.4f}→{f['lineal_despres']['B_G']:.4f} | cod R/G {f['codificat_abans']['R_G']:.4f}→"
          f"{f['codificat_despres']['R_G']:.4f} B/G {f['codificat_abans']['B_G']:.4f}→{f['codificat_despres']['B_G']:.4f}")
print(f'fet ({time.time() - T0:.0f} s)')

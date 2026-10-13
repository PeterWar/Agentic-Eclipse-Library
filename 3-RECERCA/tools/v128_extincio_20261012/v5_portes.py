"""v5 · Portes de la skill postprocessat-corona aplicades a la V128, amb veredictes separats (AGENTS.md §4.14):
mètode / llinatge, integritat del fitxer i validació visual o científica. No es força cap PASSA.
  1. Torre de Pisa: la porta executable (porta_torre_pisa.py) està lligada al contracte congelat de la V110; només se'n pot
     córrer l'autoprova. Es declara el contracte de la V128 i el veredicte de mètode: NO ÉS UNA CURA (capa a sobre del compost
     acabat; el defecte neix al compost lineal).
  2. A3 de la skill (cap retall RGB nou): es compten els píxels retallats nous (arran del limbe i lluny, amb la distància al
     cercle lunar) i els que deixen d'estar al màxim (canal per canal a la V125, i quants eren blancs del tot).
  3. Estrelles (porta_estrelles.py): demana un render natiu del Photoshop sense les capes d'estrelles → NO AVALUABLE.
  4. Photoshop (p6, porta_photoshop.sh): NO EXECUTADES (ordre: no obrir res al Photoshop).
  5. Mosaic 2×2 i balanç per canal (v1), integritat (v3), vistes (v4).
  6. (afegit el 12-10, després del segon lector) Disc lunar contra la fusionada DESADA de la V125-FINAL (no només contra la
     lectura de psd-tools); norma del rectangle al limbe (AGENTS §4.5: el cercle fix de l'e3 contra el limbe real); franja del
     moviment lunar (AGENTS §4.6); i la prova (a) de l'e1 entre les dues geometries.
Les fusionades es llegeixen en cru (psb_cru). El cel es refà amb la recepta de l'e3 (mateixos paràmetres) i es comprova que,
amb aquest cel, la recepta torna la matriu OUT al voltant de la Lluna.
Ús: PYTHONDONTWRITEBYTECODE=1 <python> v5_portes.py <carpeta_de_treball>"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

AQUI = Path(__file__).resolve().parent
ARREL = AQUI.parents[2]
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/extincio_diferencial_20261012'))
import psb_cru as pc  # noqa: E402
import ed_comu as ed  # noqa: E402

T0 = time.time()
TREB = Path(sys.argv[1]).resolve()
RES = ARREL / '3-RECERCA/resultats/v128_extincio_20261012'
SRC = ARREL / '1-PHOTOSHOP/V125-FINAL.psb'
DST = ARREL / '1-PHOTOSHOP/V128.psb'
PORTA = ARREL / '3-RECERCA/tools/guardrails_postprocessat/porta_torre_pisa.py'
CONTRACTE_V110 = ARREL / '3-RECERCA/resultats/v110_torre_20260928/CONTRACTE_TORRE.json'
v1 = json.load(open(RES / 'V1_CORRECCIO.json'))
v2 = json.load(open(RES / 'V2_PSB.json'))
v3 = json.load(open(RES / 'V3_VERIFICACIO.json'))
v4 = json.load(open(RES / 'V4_VISTES.json'))
E1 = json.load(open(ed.RES / 'E1_MASSA_AIRE_FINAL.json'))

sha_dst = ed.sha256(DST)
sha_src = ed.sha256(SRC)
integritat = dict(veredicte='PASSA' if (v3['veredicte'] == 'PASSA' and sha_dst == v3['sha256'] == v2['desti']['sha256']
                                         and sha_src == v2['font']['sha256']) else 'FALLA',
                  fitxer='1-PHOTOSHOP/V128.psb', sha256=sha_dst, sha_igual_al_verificat=sha_dst == v3['sha256'],
                  font_sense_canvis=sha_src == v2['font']['sha256'], mida=DST.stat().st_size,
                  lectors=['psd-tools 1.18 (registres, canals, capes noves, fusionada, miniatura)', 'psb_cru (lector cru propi)',
                           'sips / ImageIO de macOS (fusionada a TIFF de 16 bits)'],
                  no_fet='porta_photoshop.sh i p6 (obrir-la al Photoshop): prohibit per l\'encàrrec')

# 1. torre de Pisa
st = subprocess.run([sys.executable, str(PORTA), '--selftest'], capture_output=True, text=True, cwd=str(ARREL))
c110 = json.loads(CONTRACTE_V110.read_text())
fonts_v110 = {k: Path(c110[k]['path']).exists() for k in ('base', 'manual')}
torre = dict(
    porta=str(PORTA.relative_to(ARREL)), porta_sha256=ed.sha256(PORTA),
    autoprova=dict(codi=st.returncode, sortida=json.loads(st.stdout) if st.returncode == 0 else st.stderr[-500:]),
    porta_completa='NO APLICABLE: és lligada al contracte congelat de la V110 (V108 → V110, capes 41/42/308) i les seves fonts '
                   f'ja no són a la seva ruta ({fonts_v110}); no jutja cap altra versió',
    contracte_declarat_V128=dict(
        font=dict(psb='1-PHOTOSHOP/V125-FINAL.psb', sha256=sha_src, imatge='la fusionada (Image Data), Adobe RGB, 16 bits'),
        defecte='extinció diferencial: el costat de l\'horitzó va arribar més fosc i el del zenit més clar (Sol a 9°)',
        primer_pis_defectuos='la llum de cada fotograma; el primer pis on es pot curar és el compost lineal fusion_total_v42 '
                             '(LLEGEIX-ME_v2 de l\'extinció, «pis 1»)',
        operacio_que_el_corregeix='corona lineal (sense el cel) × E(x, y) = 10^(0,4·0,40·(X − X☉)), el mateix a R, G i B',
        passos_que_en_depenen='la base, els 16 filtres, el muntatge i totes les capes de Pere de la V125-FINAL, inclosa la «Capa 1» '
                              '(opaca, l\'acabat)',
        retocs_manuals='les 49 capes de Pere, intactes byte a byte a la V128; no s\'han refet',
        que_fa_la_V128='multiplica per E la part de corona de la imatge ACABADA (pis 2 de l\'extinció): una capa a sobre de tot'),
    veredicte_metode='NO ÉS UNA CURA. És l\'aproximació que Pere ha demanat, declarada. La porta (regles 2 i 4) diu que una capa '
                     'nova a sobre no acredita la cura d\'una capa inferior i que una compensació del compost no és una cura: '
                     'tot just això és la V128. Apagant la capa, la V128 torna a ser la V125-FINAL.')

# 2. A3: retalls nous (les dues fusionades, en cru: la desada de la V125-FINAL i la matriu de la capa nova)
p = pc.PSB(SRC)
H, W, n = p.alt, p.ample, p.alt * p.ample * 2
assert p.id_compressio == 0 and p.canals >= 4
U = np.stack([np.frombuffer(p.b, '>u2', H * W, p.id_pos + 2 + k * n).reshape(H, W) for k in range(3)], -1)
ALFA = np.frombuffer(p.b, '>u2', H * W, p.id_pos + 2 + 3 * n).reshape(H, W).copy()   # l'alfa de la fusionada desada
p.tanca()
OUT = np.load(TREB / 'OUT_rgb16.npy')
cu, co = np.any(U == 65535, axis=2), np.any(OUT == 65535, axis=2)
g = ed.geo_final()
sp = ed.Spline(ed.GRAELLA_FINAL)
LX, LY = ed.LLUNA_F
RL = ed.R_LLUNA_F                       # el cercle del disc lunar de l'e3 (R 453,64 px): allà E = 1
LLUNY = 600.0                           # px del centre lunar: més enllà, «lluny del limbe»
VZ = np.array(E1['zenit']['vector_imatge_xfila'])     # cap al zenit, en (x, fila)


def tres(m):
    return [round(float(t), 2) for t in (m.min(), np.median(m), m.max())]


def on(m):
    yy, xx = np.nonzero(m)
    if not len(yy):
        return None
    r, pa = g.polar(xx.astype(float), yy.astype(float))
    dl = np.hypot(xx - LX, yy - LY) - RL                       # distància al cercle lunar (px; > 0 fora)
    ll = dl > LLUNY - RL
    E = ed.factor_E(sp.X_punts(xx.astype(float), yy.astype(float)), sp.X_sol)
    d = dict(n=int(len(yy)), r_Rsol=[float(r.min()), float(np.median(r)), float(r.max())], PA_solar_mediana=float(np.median(pa)),
             n_arran_del_limbe=int((~ll).sum()), n_lluny_del_limbe=int(ll.sum()),
             dist_al_cercle_lunar_px_min_mediana_max=tres(dl),
             dist_al_cercle_lunar_px_arran_del_limbe=tres(dl[~ll]) if (~ll).any() else None,
             per_canal_V125=[int((U[yy, xx, c] == 65535).sum()) for c in range(3)],
             per_canal_V128=[int((OUT[yy, xx, c] == 65535).sum()) for c in range(3)],
             blancs_del_tot_V125=int(np.all(U[yy, xx] == 65535, axis=1).sum()),
             blancs_del_tot_V128=int(np.all(OUT[yy, xx] == 65535, axis=1).sum()),
             costat_del_zenit=int(((xx - LX) * VZ[0] + (yy - LY) * VZ[1] > 0).sum()),
             E_min_max=[float(E.min()), float(E.max())],
             lluny_del_limbe=[[int(x), int(y)] for x, y in zip(xx[ll], yy[ll])])
    return d


dmax = np.abs(OUT.astype(np.int32) - U.astype(np.int32)).max(axis=2)
iy, ix = np.unravel_index(int(np.argmax(dmax)), dmax.shape)
a3 = dict(criteri='skill postprocessat-corona, pas 10 / A3: cap retall RGB nou (llindar no canviat). «Retallat» = algun canal a '
                  '65.535. Les distàncies són al cercle lunar de l\'e3 (R 453,64 px; > 0 vol dir fora); «lluny» = a més de '
                  f'{LLUNY:g} px del centre lunar.',
          retallats_V125=int(cu.sum()), retallats_V128=int(co.sum()), nous=on(co & ~cu), ja_ho_eren=on(co & cu),
          deixen_d_estar_al_maxim=on(cu & ~co),
          canvi_maxim_contra_la_fusionada_desada=dict(DN16=int(dmax[iy, ix]), x=int(ix), y=int(iy),
                                                       dist_al_cercle_lunar_px=round(float(np.hypot(ix - LX, iy - LY) - RL), 1),
                                                       era_al_maxim_a_la_V125=bool(cu[iy, ix]),
                                                       px_canviats=int((dmax > 0).sum())))
a3['veredicte'] = 'FALLA' if a3['nous'] else 'PASSA'
cu_n, co_n = int(cu.sum()), int(co.sum())
del cu, co

# 6a. Disc lunar contra la fusionada DESADA (l'e3 el comprova contra la lectura de psd-tools)
M = 530                                                       # finestra al voltant de la Lluna (prou per a 496 px + marge)
x0, x1, y0, y1 = int(LX) - M, int(LX) + M + 1, int(LY) - M, int(LY) + M + 1
rows, cols = np.arange(y0, y1, dtype=np.float64), np.arange(x0, x1, dtype=np.float64)
XX, YY = np.meshgrid(cols, rows)
rl = np.hypot(XX - LX, YY - LY)
disc = rl <= RL
Uc, Oc, Ac = U[y0:y1, x0:x1].astype(np.float64), OUT[y0:y1, x0:x1].astype(np.float64), ALFA[y0:y1, x0:x1].astype(np.float64)
dd = np.abs(Oc - Uc).max(axis=2)
dif = disc & (dd > 0)
af = Ac[..., None] / 65535.0
blanc = np.round(np.clip((Uc / 65535.0 + af - 1.0) / np.maximum(af, 1e-9), 0, 1) * 65535.0)   # treure el fons blanc
dyx = np.nonzero(dif)
disc_lunar = dict(
    criteri='píxels a r ≤ 453,64 px del centre lunar de la final (el cercle de l\'e3)', n_px=int(disc.sum()),
    contra_la_lectura_de_psd_tools=dict(px_diferents=v1['proves_e3']['disc_lunar_pixels_diferents'],
                                        nota='és la prova de l\'e3: la seva entrada és la lectura de psd-tools'),
    contra_la_fusionada_desada=dict(
        px_diferents=int(dif.sum()), max_DN16=int(dd[dif].max()) if dif.any() else 0,
        mediana_DN16=float(np.median(dd[dif])) if dif.any() else 0.0,
        x_min_max=[int(XX[dif].min()), int(XX[dif].max())] if dif.any() else None,
        y_min_max=[int(YY[dif].min()), int(YY[dif].max())] if dif.any() else None,
        dist_al_centre_lunar_px=[round(float(rl[dif].min()), 1), round(float(rl[dif].max()), 1)] if dif.any() else None,
        alfa_min_max=[int(Ac[dif].min()), int(Ac[dif].max())] if dif.any() else None,
        tots_amb_alfa_no_plena=bool((Ac[dif] < 65535).all()) if dif.any() else None,
        alfa_no_plena_al_disc=int((disc & (Ac < 65535)).sum()), alfa_no_plena_a_tot_el_llenc=int((ALFA < 65535).sum()),
        alfa_minima_del_llenc=int(ALFA.min()),
        iguals_a_treure_el_fons_blanc=int((np.abs(blanc - Oc).max(axis=2)[dif] == 0).sum()),
        max_DN16_contra_treure_el_fons_blanc=int(np.abs(blanc - Oc).max(axis=2)[dif].max()) if dif.any() else 0),
    explicacio='La V125-FINAL desa a la fusionada 749 píxels gairebé opacs (alfa 65.505–65.534), al limbe est. psd-tools els '
               'llegeix traient-los el fons blanc, (c + a − 1)/a, i l\'e3 va partir d\'aquests valors. Dins del disc l\'e3 no '
               'canvia res respecte de la seva entrada, però sí que difereix, poc, de la fusionada desada.')
del ALFA

# 6b. Norma del rectangle al limbe (AGENTS §4.5): el cercle fix contra el limbe real
hb, wb = H // 8, W // 8                                       # el cel de l'e3, refet amb la mateixa recepta i paràmetres
lin_b = ((U[:hb * 8, :wb * 8].astype(np.float64) / 65535.0) ** ed.GAMMA).reshape(hb, 8, wb, 8, 3).mean(axis=(1, 3))
XB, YB = np.meshgrid(np.arange(wb) * 8 + 3.5, np.arange(hb) * 8 + 3.5)
rb, _ = g.polar(XB, YB)
pp = pc.PSB(SRC)
icc = [bytes(pp.b[r['dades']:r['dades'] + r['mida']]) for r in pp.recursos if r['id'] == 1039][0]
pp.tanca()
YC = np.array(ed.info_icc(icc)['Y'])
Yb = lin_b @ YC
res_ = Yb - nd.median_filter(Yb, size=7)
zs = rb > 4.0
sd = 1.4826 * np.median(np.abs(res_[zs] - np.median(res_[zs])))
sel = (rb >= 6.0) & ~nd.binary_dilation((res_ > 5 * sd) & (rb > 3.0), iterations=2)


def termes(x, y):
    u_, v_ = (np.asarray(x, np.float64) - g.cx) / g.R, (np.asarray(y, np.float64) - g.cy) / g.R
    return [np.ones_like(u_), u_, v_, u_ * u_, u_ * v_, v_ * v_]


TB = termes(XB, YB)
Am = np.stack([t[sel] for t in TB], 1)
coef = []
for c in range(3):
    yv = lin_b[..., c][sel]
    w = np.ones(len(yv), bool)
    for _ in range(6):
        cf, *_ = np.linalg.lstsq(Am[w], yv[w], rcond=None)
        rr = yv - Am @ cf
        md = np.median(rr[w])
        s_ = 1.4826 * np.median(np.abs(rr[w] - md))
        w = (rr - md < 2.5 * s_) & (rr - md > -4.0 * s_)
    coef.append(cf)
coef = np.array(coef)
del lin_b
TT = termes(XX, YY)
S = np.stack([sum(coef[c, i] * TT[i] for i in range(6)) for c in range(3)], axis=-1)
lin = (Uc / 65535.0) ** ed.GAMMA
E = ed.factor_E(sp.X_graella(rows, cols), sp.X_sol)
lin2 = S + np.where(disc, 1.0, E)[..., None] * (lin - S)
o = np.round(np.clip(lin2, 0, 1) ** (1 / ed.GAMMA) * 65535.0)
plena = Ac >= 65535
repro = dict(px=int(plena.sum()), px_diferents=int((np.abs(o - Oc).max(axis=2)[plena] > 0).sum()),
             max_DN16=int(np.abs(o - Oc).max(axis=2)[plena].max()))
Y = lin @ YC
Ys = S @ YC
Yo = ((Oc / 65535.0) ** ed.GAMMA) @ YC
dz = ((XX - LX) * VZ[0] + (YY - LY) * VZ[1]) / np.maximum(rl, 1e-9)    # cosinus de l'angle amb el zenit, des del centre lunar
ang = np.degrees(np.arctan2(YY - LY, XX - LX)) % 360.0                 # angle a la imatge (0 = +x; 90 = cap avall)
radis = []
for s in range(36):                                            # limbe real per sectors de 10°: on la lluminància lineal passa
    msec = (ang >= 10 * s) & (ang < 10 * s + 10) & (rl >= 420) & (rl <= 480)   # del 50 % entre el disc (420–440 px) i el pic
    rbin = np.floor((rl[msec] - 420) / 0.5).astype(int)        # de fora (448–480 px), amb perfils de 0,5 px (mediana)
    yv = Y[msec]
    prof = np.array([np.median(yv[rbin == k]) if (rbin == k).any() else np.nan for k in range(120)])
    rc = 420 + 0.5 * np.arange(120) + 0.25
    yin = np.nanmedian(prof[(rc >= 420) & (rc <= 440)])
    pk = np.nanmax(prof[(rc >= 448) & (rc <= 480)])
    thr = yin + 0.5 * (pk - yin)
    sobre = (rc >= 440) & (prof >= thr)
    assert sobre.any(), f'sector {s}: cap radi passa del 50 %'
    k0 = int(np.argmax(sobre))
    r50 = rc[k0 - 1] + (thr - prof[k0 - 1]) / (prof[k0] - prof[k0 - 1]) * 0.5 if prof[k0] != prof[k0 - 1] else rc[k0]
    radis.append(float(r50))
radis = np.array(radis)
dins_dada = disc & (Y > Ys)
dins_005 = disc & (Y > 0.05)
fora2 = (rl > RL) & (rl <= RL + 2)
fora_fosc = (rl > RL) & (rl <= RL + 20) & (Y <= Ys)
dDN = np.abs(Oc - Uc).max(axis=2)


def costat(m, signe):
    return m & ((dz > 0.866) if signe > 0 else (dz < -0.866))   # ±30° al voltant del zenit o de l'horitzó


limbe = dict(
    norma='AGENTS §4.5: un filtre s\'aplica a tot el rectangle; només el pot aturar que no hi hagi dada',
    que_fa_l_e3='E = 1 dins d\'un cercle fix (centre de la Lluna de C2 de Pere, R 453,64 px); fora, cel + E·(lin − cel)',
    reproduccio_de_l_e3_amb_el_cel_refet=dict(repro, nota='finestra de ±530 px al voltant de la Lluna, píxels amb alfa plena'),
    limbe_real_px=dict(criteri='per sectors de 10° al voltant del centre lunar: radi on la lluminància lineal passa del 50 % entre '
                               'el disc (420–440 px) i el pic de fora (448–480 px); perfil de medianes cada 0,5 px',
                       min=round(float(radis.min()), 2), mediana=round(float(np.median(radis)), 2), max=round(float(radis.max()), 2),
                       sectors_amb_el_limbe_dins_del_cercle=int((radis < RL).sum()), sectors=36,
                       per_sector_graus_imatge=[round(float(r_), 2) for r_ in radis]),
    corona_dins_del_cercle_sense_corregir=dict(
        Y_mes_gran_de_0_05=int(dins_005.sum()), Y_per_sobre_del_cel=int(dins_dada.sum()),
        cel_Y_al_limbe=round(float(np.median(Ys[fora2])), 4),
        dist_al_cercle_px_Y_0_05=tres(RL - rl[dins_005]) if dins_005.any() else None,
        costat_del_zenit_Y_0_05=int((dins_005 & (dz > 0)).sum()), costat_de_l_horitzo_Y_0_05=int((dins_005 & (dz < 0)).sum()),
        a_30_graus_del_zenit_Y_0_05=int(costat(dins_005, 1).sum()), a_30_graus_de_l_horitzo_Y_0_05=int(costat(dins_005, -1).sum())),
    grao_just_fora_del_cercle=dict(
        criteri='E als píxels a 0–2 px fora del cercle (dins, E = 1)', E_min=round(float(E[fora2].min()), 4),
        E_max=round(float(E[fora2].max()), 4),
        quocient_lluminancia_V128_V125_corona_zenit=round(float(np.median((Yo / Y)[costat(fora2 & (Y > 0.05), 1)])), 4),
        quocient_lluminancia_V128_V125_corona_horitzo=round(float(np.median((Yo / Y)[costat(fora2 & (Y > 0.05), -1)])), 4)),
    fosc_fora_del_cercle=dict(
        criteri='píxels a 0–20 px fora del cercle amb la lluminància lineal per sota del cel (disc fosc, sense corona) que sí '
                'que es corregeixen', n=int(fora_fosc.sum()), max_DN16=int(dDN[fora_fosc].max()) if fora_fosc.any() else 0,
        mediana_DN16=float(np.median(dDN[fora_fosc])) if fora_fosc.any() else 0.0),
    veredicte='FALLA LOCAL' if dins_dada.any() else 'PASSA',
    lectura='El cercle fix no és el limbe de la final: deixa sense corregir 1–3 px de corona dins del cercle i, just fora, el '
            'guany és E. Fa un anell d\'1–2 px amb un graó de l\'ordre de ±5–6 %. A 6× no es veu, però va contra la norma del '
            'rectangle. Refer la capa aturant la correcció per dada (lluminància ≤ cel) a la vora del limbe, o amb el limbe '
            'mesurat, és una decisió de Pere: canviaria només aquests píxels.')

# 6c. Franja del moviment lunar (AGENTS §4.6: r ≈ 456–496 px, no entra a cap filtre)
fr = (rl >= 456) & (rl <= 496)
var = []
for s in range(36):
    msec = (ang >= 10 * s) & (ang < 10 * s + 10)
    e_in, e_out = np.median(E[msec & (rl >= 456) & (rl <= 460)]), np.median(E[msec & (rl >= 492) & (rl <= 496)])
    var.append(abs(e_out / e_in - 1))
franja = dict(norma='AGENTS §4.6: la franja del moviment lunar (r ≈ 456–496 px) no entra a cap filtre',
              px_franja=int(fr.sum()), px_canviats=int((fr & (dDN > 0)).sum()), E_min_max=[round(float(E[fr].min()), 4),
                                                                                         round(float(E[fr].max()), 4)],
              variacio_max_d_E_a_traves_de_la_franja=round(float(max(var)), 5),
              veredicte='DECLARADA',
              lectura='La correcció hi entra, com a tot el rectangle. No és un filtre d\'estructura: cada píxel es multiplica per la '
                      'seva E, sense barrejar-lo amb els veïns, i E hi varia com a molt el que diu variacio_max_d_E_a_traves_de_la_franja.')
del Uc, Oc, Ac, U, OUT

# 6d. La prova (a) de l'e1: les dues geometries
pa_ = E1['prova_a_contra_llenc_V42']
e1a = dict(passa=pa_['passa'], max_abs_dX=pa_['max_abs_dX'], llindar_dX=0.005, max_abs_dE=pa_['max_abs_dE'],
           lectura='Les geometries de la final i del llenç V42 donen la mateixa X al centre del Sol i difereixen com a molt 0,0051 '
                   'a les cantonades (llindar 0,005): E canvia com a molt un 0,19 %. Es declara; no canvia cap xifra del rebut.')

estrelles = dict(porta='.claude/skills/postprocessat-corona/scripts/porta_estrelles.py', veredicte='NO AVALUABLE',
                 motiu='demana el render natiu del Photoshop sense les capes d\'estrelles; l\'encàrrec prohibeix obrir el Photoshop',
                 fets='cap estrella afegida, treta ni moguda; la seva llum (per sobre del cel estimat) es multiplica per la mateixa E '
                      'que la corona, com fa l\'atmosfera; la capa de Pere amb les estrelles és intacta')
photoshop = dict(p6='NO EXECUTADA', porta_photoshop_sh='NO EXECUTADA',
                 motiu='l\'encàrrec prohibeix obrir, tancar o desar res al Photoshop i fer córrer JSX',
                 substitut_parcial='tres lectors independents (v3); el lector de debò és el Photoshop, i no s\'ha provat')
visual = dict(veredicte='PENDENT DE PERE', vistes=v4['vistes'],
              nota='l\'agent ha mirat les vistes i el limbe a 1:1, i el segon lector, a 6×: no s\'hi veu cap vora. Però el cercle '
                   'fix de l\'e3 deixa un anell d\'1–2 px amb un graó de l\'ordre de ±5–6 % (vegeu limbe_rectangle). No és cap '
                   'validació científica')
info = dict(guio=str(Path(__file__).resolve().relative_to(ARREL)), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
            veredictes=dict(metode=torre['veredicte_metode'], integritat=integritat['veredicte'], a3_retall_nou=a3['veredicte'],
                            rectangle_al_limbe=limbe['veredicte'], franja_lunar=franja['veredicte'],
                            estrelles=estrelles['veredicte'], photoshop='NO EXECUTADA', visual_o_cientific=visual['veredicte']),
            integritat=integritat, torre_de_pisa=torre, a3=a3, disc_lunar=disc_lunar, limbe_rectangle=limbe,
            franja_lunar=franja, e1_prova_a=e1a, estrelles=estrelles, photoshop=photoshop,
            mosaic_i_balanc=dict(mosaic_2x2_DN16=v1['matriu']['mosaic_2x2_DN16'], balanc=v1['matriu']['balanc_per_canal_tot_el_llenc']),
            proves_e3=v1['proves_e3'], reproduccio=v1['reproduccio'], visual=visual, segons=round(time.time() - T0, 1))
json.dump(info, open(RES / 'V5_PORTES.json', 'w'), indent=1, ensure_ascii=False, default=str)
print(json.dumps(dict(veredictes=info['veredictes'], a3={k: v for k, v in a3.items() if k != 'deixen_d_estar_al_maxim'},
                      deixen={k: v for k, v in (a3['deixen_d_estar_al_maxim'] or {}).items() if k != 'lluny_del_limbe'},
                      disc_lunar=disc_lunar, limbe=limbe, franja=franja, e1a=e1a, integritat=integritat),
                 indent=1, ensure_ascii=False, default=str))

"""v5b · Portes de la skill postprocessat-corona aplicades a la V128 NOVA (regla del limbe, 12-10-2026), amb veredictes separats
(AGENTS.md §4.14): mètode / llinatge, integritat del fitxer i validació visual o científica. No es força cap PASSA.
És el v5 amb les entrades noves (OUTB del v1b, V2B/V3B/V4B) i amb la secció del limbe refeta per a la regla predeclarada
(PREDECLARACIO_LIMBE.md):
  1. Torre de Pisa: com el v5 (només l'autoprova de la porta; contracte declarat; NO ÉS UNA CURA).
  2. A3 (cap retall RGB nou): retallats de la V128 nova contra la fusionada DESADA de la V125-FINAL, i contra la capa anterior.
  3. Estrelles: NO AVALUABLE (demana un render del Photoshop). 4. Photoshop: NO EXECUTADES.
  5. Integritat (v3b), vistes (v4b), mosaic i balanç (v1b).
  6a. Disc lunar contra la fusionada desada: el que la regla deixa intacte (r < 440 px, i a l'anell els píxels sense dada).
  6b. Norma del rectangle al limbe: la capa refeta al voltant de la Lluna des dels FITXERS (la fusionada desada de la V125-FINAL
      i la de la V128 llegides en cru), amb el cel refet per la recepta de l'e3; corona sense corregir a r ≥ 440 px; foscos
      canviats; l'anell d'abans (quocient a banda i banda del cercle de l'e3, abans i ara).
  6c. Franja del moviment lunar (AGENTS §4.6). 6d. La prova (a) de l'e1.
Els 749 píxels de la fusionada de la V125-FINAL amb alfa no plena (al limbe est): psd-tools els llegeix traient-los el fons
blanc, (c + a − 1)/a, i l'e3 (i per tant el v1b) parteix d'aquests valors. Aquí es fa el mateix per comparar-los amb la regla.
Ús: PYTHONDONTWRITEBYTECODE=1 <python> v5b_portes.py <carpeta_de_treball>"""
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
v1b = json.load(open(RES / 'V1B_CORRECCIO_LIMBE.json'))
v2 = json.load(open(RES / 'V2B_PSB.json'))
v3 = json.load(open(RES / 'V3B_VERIFICACIO.json'))
v4 = json.load(open(RES / 'V4B_VISTES.json'))
E1 = json.load(open(ed.RES / 'E1_MASSA_AIRE_FINAL.json'))
R_INT, R_EXT = v1b['regla']['R_INT'], v1b['regla']['R_EXT']

sha_dst = ed.sha256(DST)
sha_src = ed.sha256(SRC)
integritat = dict(veredicte='PASSA' if (v3['veredicte'] == 'PASSA' and sha_dst == v3['sha256'] == v2['desti']['sha256']
                                         and sha_src == v2['font']['sha256']) else 'FALLA',
                  fitxer='1-PHOTOSHOP/V128.psb', sha256=sha_dst, sha_igual_al_verificat=sha_dst == v3['sha256'],
                  font_sense_canvis=sha_src == v2['font']['sha256'], mida=DST.stat().st_size,
                  lectors=['psd-tools 1.18 (registres, canals, capes noves, fusionada, miniatura)', 'psb_cru (lector cru propi)',
                           'sips / ImageIO de macOS (fusionada a TIFF de 16 bits)', 'ael.photoshop.verify() (51 capes; A i B píxel a píxel)'],
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
        que_fa_la_V128=('multiplica per E la part de corona de la imatge ACABADA (pis 2 de l\'extinció): una capa a sobre de tot; '
                        f'arran del limbe ({R_INT:g}–{R_EXT:g} px), només on hi ha senyal de corona (Y > cel), regla predeclarada')),
    veredicte_metode='NO ÉS UNA CURA. És l\'aproximació que Pere ha demanat, declarada. La porta (regles 2 i 4) diu que una capa '
                     'nova a sobre no acredita la cura d\'una capa inferior i que una compensació del compost no és una cura: '
                     'tot just això és la V128. Apagant la capa, la V128 torna a ser la V125-FINAL.')

# 2. A3: retalls nous (la fusionada desada de la V125-FINAL contra la fusionada DESADA de la V128 nova, totes dues en cru)
p = pc.PSB(SRC)
H, W, n = p.alt, p.ample, p.alt * p.ample * 2
assert p.id_compressio == 0 and p.canals >= 4
U = np.stack([np.frombuffer(p.b, '>u2', H * W, p.id_pos + 2 + k * n).reshape(H, W) for k in range(3)], -1)
ALFA = np.frombuffer(p.b, '>u2', H * W, p.id_pos + 2 + 3 * n).reshape(H, W).copy()
icc = [bytes(p.b[r['dades']:r['dades'] + r['mida']]) for r in p.recursos if r['id'] == 1039][0]
q = pc.PSB(DST)
assert q.id_compressio == 0 and (q.alt, q.ample) == (H, W)
OUT = np.stack([np.frombuffer(q.b, '>u2', H * W, q.id_pos + 2 + k * n).reshape(H, W) for k in range(3)], -1).astype(np.uint16)
q.tanca()
assert hashlib.sha256(np.ascontiguousarray(OUT).tobytes()).hexdigest() == v1b['matriu']['sha256_bytes_OUTB'], 'fusionada ≠ OUTB'
VELL = np.load(TREB / 'OUT_rgb16.npy')                      # la capa A anterior (la V128 retirada), per contrast
assert hashlib.sha256(np.ascontiguousarray(VELL).tobytes()).hexdigest() == v1['matriu']['sha256_bytes_OUT']
cu, co, cv = np.any(U == 65535, axis=2), np.any(OUT == 65535, axis=2), np.any(VELL == 65535, axis=2)
g = ed.geo_final()
sp = ed.Spline(ed.GRAELLA_FINAL)
LX, LY = ed.LLUNA_F
RL = ed.R_LLUNA_F
LLUNY = 600.0
VZ = np.array(E1['zenit']['vector_imatge_xfila'])


def tres(m):
    return [round(float(t), 2) for t in (m.min(), np.median(m), m.max())]


def on(m):
    yy, xx = np.nonzero(m)
    if not len(yy):
        return None
    r, pa = g.polar(xx.astype(float), yy.astype(float))
    dl = np.hypot(xx - LX, yy - LY)
    ll = dl > LLUNY
    E = ed.factor_E(sp.X_punts(xx.astype(float), yy.astype(float)), sp.X_sol)
    return dict(n=int(len(yy)), r_Rsol=[float(r.min()), float(np.median(r)), float(r.max())], PA_solar_mediana=float(np.median(pa)),
                n_arran_del_limbe=int((~ll).sum()), n_lluny_del_limbe=int(ll.sum()),
                dist_al_centre_lunar_px_min_mediana_max=tres(dl),
                per_canal_V125=[int((U[yy, xx, c] == 65535).sum()) for c in range(3)],
                per_canal_V128=[int((OUT[yy, xx, c] == 65535).sum()) for c in range(3)],
                blancs_del_tot_V125=int(np.all(U[yy, xx] == 65535, axis=1).sum()),
                blancs_del_tot_V128=int(np.all(OUT[yy, xx] == 65535, axis=1).sum()),
                costat_del_zenit=int(((xx - LX) * VZ[0] + (yy - LY) * VZ[1] > 0).sum()),
                E_min_max=[float(E.min()), float(E.max())],
                lluny_del_limbe=[[int(x), int(y)] for x, y in zip(xx[ll], yy[ll])],
                arran_del_limbe=[[int(x), int(y), round(float(d), 2)] for x, y, d in zip(xx[~ll], yy[~ll], dl[~ll])][:300])


dmax = np.abs(OUT.astype(np.int32) - U.astype(np.int32)).max(axis=2)
iy, ix = np.unravel_index(int(np.argmax(dmax)), dmax.shape)
a3 = dict(criteri='skill postprocessat-corona, pas 10 / A3: cap retall RGB nou (llindar no canviat). «Retallat» = algun canal a '
                  f'65.535. «Lluny» = a més de {LLUNY:g} px del centre lunar; si no, «arran del limbe».',
          retallats_V125=int(cu.sum()), retallats_V128=int(co.sum()), retallats_V128_anterior=int(cv.sum()),
          nous=on(co & ~cu), ja_ho_eren=on(co & cu), deixen_d_estar_al_maxim=on(cu & ~co),
          nous_respecte_de_la_V128_anterior=on(co & ~cv), la_V128_anterior_i_ara_no=on(cv & ~co),
          canvi_maxim_contra_la_fusionada_desada=dict(DN16=int(dmax[iy, ix]), x=int(ix), y=int(iy),
                                                       dist_al_centre_lunar_px=round(float(np.hypot(ix - LX, iy - LY)), 1),
                                                       era_al_maxim_a_la_V125=bool(cu[iy, ix]),
                                                       px_canviats=int((dmax > 0).sum())))
a3['veredicte'] = 'FALLA' if a3['nous'] else 'PASSA'
del cu, co, cv, dmax

# 6. Finestra al voltant de la Lluna: el cel de l'e3 refet, l'entrada de l'e3 (fons blanc tret on l'alfa no és plena)
hb, wb = H // 8, W // 8
lin_b = ((U[:hb * 8, :wb * 8].astype(np.float64) / 65535.0) ** ed.GAMMA).reshape(hb, 8, wb, 8, 3).mean(axis=(1, 3))
XB, YB = np.meshgrid(np.arange(wb) * 8 + 3.5, np.arange(hb) * 8 + 3.5)
rb, _ = g.polar(XB, YB)
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
M = 530
x0, x1, y0, y1 = int(LX) - M, int(LX) + M + 1, int(LY) - M, int(LY) + M + 1
rows, cols = np.arange(y0, y1, dtype=np.float64), np.arange(x0, x1, dtype=np.float64)
XX, YY = np.meshgrid(cols, rows)
rl = np.hypot(XX - LX, YY - LY)
Uc, Oc, Vc = U[y0:y1, x0:x1].astype(np.float64), OUT[y0:y1, x0:x1].astype(np.float64), VELL[y0:y1, x0:x1].astype(np.float64)
Ac = ALFA[y0:y1, x0:x1].astype(np.float64)
plena = Ac >= 65535
af = Ac[..., None] / 65535.0
blanc = np.round(np.clip((Uc / 65535.0 + af - 1.0) / np.maximum(af, 1e-9), 0, 1) * 65535.0)
Ui = np.where(plena[..., None], Uc, blanc)                     # l'entrada de l'e3 (la lectura de psd-tools), refeta
TT = termes(XX, YY)
S = np.stack([sum(coef[c, i] * TT[i] for i in range(6)) for c in range(3)], axis=-1)
lin = (Ui / 65535.0) ** ed.GAMMA
E = ed.factor_E(sp.X_graella(rows, cols), sp.X_sol)
Y = lin @ YC
Ys = S @ YC
dada = Y > Ys
inter, anell, fora = rl < R_INT, (rl >= R_INT) & (rl <= R_EXT), rl > R_EXT
intacte = inter | (anell & ~dada)
lin2 = S + np.where(intacte, 1.0, E)[..., None] * (lin - S)
o = np.round(np.clip(lin2, 0, 1) ** (1 / ed.GAMMA) * 65535.0)
o = np.where(intacte[..., None], Ui, o)
dO = np.abs(o - Oc).max(axis=2)
repro = dict(criteri=f'la regla refeta des de la fusionada desada de la V125-FINAL (fons blanc tret on l\'alfa no és plena) i el cel refet, '
                     f'contra la fusionada desada de la V128; finestra de ±{M} px al voltant de la Lluna',
             px=int(plena.size), px_diferents_alfa_plena=int((dO[plena] > 0).sum()), max_DN16_alfa_plena=int(dO[plena].max()),
             px_alfa_no_plena=int((~plena).sum()), px_diferents_alfa_no_plena=int((dO[~plena] > 0).sum()),
             max_DN16_alfa_no_plena=int(dO[~plena].max()) if (~plena).any() else 0)
print(f'reproducció de la regla des dels fitxers: {repro} ({time.time() - T0:.0f} s)', flush=True)

# 6a. Disc lunar i píxels sense dada, contra la fusionada DESADA
dU = np.abs(Oc - Uc).max(axis=2)
dUi = np.abs(Oc - Ui).max(axis=2)
disc_lunar = dict(
    criteri=f'el que la regla deixa intacte: r < {R_INT:g} px, i a l\'anell {R_INT:g}–{R_EXT:g} px els píxels sense dada (Y ≤ cel)',
    n_px=int(intacte.sum()), interior=int(inter.sum()), anell_sense_dada=int((anell & ~dada).sum()),
    contra_l_entrada_de_l_e3=dict(px_diferents=int((intacte & (dUi > 0)).sum()),
                                  nota='l\'entrada de l\'e3 és la lectura de psd-tools; aquí, refeta traient el fons blanc'),
    contra_la_fusionada_desada=dict(px_diferents=int((intacte & (dU > 0)).sum()),
                                    max_DN16=int(dU[intacte & (dU > 0)].max()) if (intacte & (dU > 0)).any() else 0,
                                    tots_amb_alfa_no_plena=bool((~plena[intacte & (dU > 0)]).all()) if (intacte & (dU > 0)).any() else None),
    alfa_no_plena=dict(a_la_finestra=int((~plena).sum()), al_llenc=int((ALFA < 65535).sum()),
                       intactes=int((~plena & intacte).sum()), corregits_amb_dada=int((~plena & ~intacte).sum()),
                       dist_al_centre_lunar_px=tres(rl[~plena]) if (~plena).any() else None),
    explicacio='La V125-FINAL desa a la fusionada 749 píxels gairebé opacs (alfa 65.505–65.534), al limbe est. psd-tools els llegeix '
               'traient-los el fons blanc, (c + a − 1)/a, i l\'e3 parteix d\'aquests valors. Els intactes són idèntics a aquesta lectura, '
               'no a la fusionada desada (com a la V128 anterior).')
del ALFA

# 6b. Norma del rectangle al limbe
ang = np.degrees(np.arctan2(YY - LY, XX - LX)) % 360.0
dz = ((XX - LX) * VZ[0] + (YY - LY) * VZ[1]) / np.maximum(rl, 1e-9)
radis = []
for s in range(36):                                            # limbe real per sectors de 10° (criteri del v5)
    msec = (ang >= 10 * s) & (ang < 10 * s + 10) & (rl >= 420) & (rl <= 480)
    rbin = np.floor((rl[msec] - 420) / 0.5).astype(int)
    yv = Y[msec]
    prof = np.array([np.median(yv[rbin == k]) if (rbin == k).any() else np.nan for k in range(120)])
    rc = 420 + 0.5 * np.arange(120) + 0.25
    yin = np.nanmedian(prof[(rc >= 420) & (rc <= 440)])
    pk = np.nanmax(prof[(rc >= 448) & (rc <= 480)])
    thr = yin + 0.5 * (pk - yin)
    sobre = (rc >= 440) & (prof >= thr)
    k0 = int(np.argmax(sobre))
    radis.append(float(rc[k0 - 1] + (thr - prof[k0 - 1]) / (prof[k0] - prof[k0 - 1]) * 0.5 if prof[k0] != prof[k0 - 1] else rc[k0]))
radis = np.array(radis)
Yo = ((Oc / 65535.0) ** ed.GAMMA) @ YC
Yv = ((Vc / 65535.0) ** ed.GAMMA) @ YC
pot = (Y - Ys > 0.002) & (np.abs(E - 1) > 0.01)               # corona on la correcció es veu a 16 bits
sense_n = pot & (rl >= R_INT) & (dUi == 0)
sense_v = pot & (rl >= R_INT) & (np.abs(Vc - Ui).max(axis=2) == 0)
fosc_anell = anell & ~dada
vf = (rl > RL) & (rl <= RL + 20) & ~dada


def costat(m, signe):
    return m & ((dz > 0.866) if signe > 0 else (dz < -0.866))


cor05 = Y > 0.05
dins_c = cor05 & (rl > RL - 3.4) & (rl <= RL)
fora_c = cor05 & (rl > RL) & (rl <= RL + 2)
anell_vell = {}
for nom, Yx in (('V128_anterior', Yv), ('V128_nova', Yo)):
    anell_vell[nom] = {f'{zona}_{costat_}': round(float(np.median((Yx / Y)[costat(m, sg)])), 4)
                       for zona, m in (('dins_del_cercle_0_3_4_px', dins_c), ('fora_del_cercle_0_2_px', fora_c))
                       for costat_, sg in (('zenit', 1), ('horitzo', -1))}
illes = inter & dada
limbe = dict(
    norma='AGENTS §4.5: un filtre s\'aplica a tot el rectangle; només el pot aturar que no hi hagi dada',
    regla=(f'r < {R_INT:g} px: intacte; {R_INT:g}–{R_EXT:g} px: E si Y > cel, intacte si Y ≤ cel; r > {R_EXT:g} px: E com l\'e3 '
           '(PREDECLARACIO_LIMBE.md)'),
    reproduccio_des_dels_fitxers=repro,
    limbe_real_px=dict(criteri='per sectors de 10° al voltant del centre lunar: radi on la lluminància lineal passa del 50 % entre '
                               'el disc (420–440 px) i el pic de fora (448–480 px); perfil de medianes cada 0,5 px',
                       min=round(float(radis.min()), 2), mediana=round(float(np.median(radis)), 2), max=round(float(radis.max()), 2),
                       marge_interior_px=round(float(radis.min() - R_INT), 2), marge_exterior_px=round(float(R_EXT - radis.max()), 2),
                       per_sector_graus_imatge=[round(float(r_), 2) for r_ in radis]),
    corona_sense_corregir=dict(criteri=f'r ≥ {R_INT:g} px, Y − cel > 0,002 i |E − 1| > 0,01 (la correcció es veu a 16 bits), '
                                       'píxel idèntic a l\'entrada', V128_nova=int(sense_n.sum()), V128_anterior=int(sense_v.sum())),
    foscos=dict(anell_sense_dada=int(fosc_anell.sum()), canviats_contra_l_entrada=int((fosc_anell & (dUi > 0)).sum()),
                els_del_v5=dict(criteri='453,64 < r ≤ 473,64 px i Y ≤ cel (la definició del v5)', n=int(vf.sum()),
                                canviats_V128_nova=int((vf & (dUi > 0)).sum()),
                                canviats_V128_anterior=int((vf & (np.abs(Vc - Ui).max(axis=2) > 0)).sum()))),
    anell_d_abans=dict(criteri='mediana del quocient de lluminància (després / abans) de la corona (Y > 0,05) a banda i banda del cercle '
                               'de l\'e3, ±30° al voltant del zenit i de l\'horitzó (des del centre lunar)', **anell_vell),
    disc_amb_llum_per_sobre_del_cel=dict(
        criteri=f'r < {R_INT:g} px i Y > cel: llum del disc de la Lluna de Pere (intacta; secció 5b de la predeclaració)',
        n=int(illes.sum()), r_min_max=[round(float(rl[illes].min()), 1), round(float(rl[illes].max()), 1)] if illes.any() else None,
        canviats=int((illes & (dUi > 0)).sum())),
    veredicte='PASSA' if (repro['px_diferents_alfa_plena'] == 0 and sense_n.sum() == 0 and (fosc_anell & (dUi > 0)).sum() == 0
                          and (vf & (dUi > 0)).sum() == 0 and (illes & (dUi > 0)).sum() == 0) else 'FALLA',
    lectura=('La correcció arriba fins on s\'acaba la dada de corona i s\'hi atura sola: el canvi, (E − 1)·(lin − cel), tendeix a zero '
             'quan la llum baixa fins al cel. Cap píxel de corona a r ≥ 440 px no queda sense corregir, cap píxel fosc del disc no canvia, '
             'i el quocient ja no fa graó al cercle de l\'e3. El salt del quocient només és on s\'acaba la dada.'))

# 6c. Franja del moviment lunar
dDN = np.abs(Oc - Ui).max(axis=2)
fr = (rl >= 456) & (rl <= 496)
var = []
for s in range(36):
    msec = (ang >= 10 * s) & (ang < 10 * s + 10)
    e_in, e_out = np.median(E[msec & (rl >= 456) & (rl <= 460)]), np.median(E[msec & (rl >= 492) & (rl <= 496)])
    var.append(abs(e_out / e_in - 1))
franja = dict(norma='AGENTS §4.6: la franja del moviment lunar (r ≈ 456–496 px) no entra a cap filtre',
              px_franja=int(fr.sum()), px_canviats=int((fr & (dDN > 0)).sum()), px_sense_dada_intactes=int((fr & intacte).sum()),
              E_min_max=[round(float(E[fr].min()), 4), round(float(E[fr].max()), 4)],
              variacio_max_d_E_a_traves_de_la_franja=round(float(max(var)), 5), veredicte='DECLARADA',
              lectura='La correcció hi entra, com a tot el rectangle. No és un filtre d\'estructura: cada píxel es multiplica per la seva '
                      'E, sense barrejar-lo amb els veïns, i E hi varia com a molt el que diu variacio_max_d_E_a_traves_de_la_franja.')
del Uc, Oc, Vc, Ac, U, OUT, VELL

# 6d. La prova (a) de l'e1
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
                 substitut_parcial='quatre lectors independents (v3b); el lector de debò és el Photoshop, i no s\'ha provat')
visual = dict(veredicte='PENDENT DE PERE', vistes=v4['vistes'],
              nota='l\'agent ha mirat les vistes a la meitat i el gràfic del perfil del limbe (b05); no s\'hi veu cap vora. No és cap '
                   'validació científica')
info = dict(guio=str(Path(__file__).resolve().relative_to(ARREL)), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
            veredictes=dict(metode=torre['veredicte_metode'], integritat=integritat['veredicte'], a3_retall_nou=a3['veredicte'],
                            rectangle_al_limbe=limbe['veredicte'], franja_lunar=franja['veredicte'],
                            estrelles=estrelles['veredicte'], photoshop='NO EXECUTADA', visual_o_cientific=visual['veredicte'],
                            proves_predeclarades_v1b=v1b['veredicte']),
            integritat=integritat, torre_de_pisa=torre, a3=a3, disc_lunar=disc_lunar, limbe_rectangle=limbe,
            franja_lunar=franja, e1_prova_a=e1a, estrelles=estrelles, photoshop=photoshop,
            mosaic_i_balanc=v1b['proves']['P10_mosaic_i_balanc'], proves_e3=v1['proves_e3'], visual=visual,
            segons=round(time.time() - T0, 1))
json.dump(info, open(RES / 'V5B_PORTES.json', 'w'), indent=1, ensure_ascii=False, default=str)
print(json.dumps(dict(veredictes=info['veredictes'],
                      a3={k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk not in ('lluny_del_limbe', 'arran_del_limbe')})
                          for k, v in a3.items()},
                      disc_lunar=disc_lunar, limbe={k: v for k, v in limbe.items() if k != 'limbe_real_px'},
                      limbe_real={k: v for k, v in limbe['limbe_real_px'].items() if k != 'per_sector_graus_imatge'},
                      franja=franja, integritat=integritat), indent=1, ensure_ascii=False, default=str))

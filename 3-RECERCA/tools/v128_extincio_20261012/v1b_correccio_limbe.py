"""v1b · La capa A de la V128 refeta amb la regla del limbe PREDECLARADA (12-10-2026).

Regla (resultats/v128_extincio_20261012/PREDECLARACIO_LIMBE.md, escrita abans de calcular res; se'n desa el SHA):
  r = distància al centre de la Lluna de C2 de Pere (GEOMETRIA_FINAL.json);
  · r < R_INT (440 px): res, el píxel surt idèntic a l'entrada;
  · R_INT ≤ r ≤ R_EXT (440–470 px): si Y > Ys (hi ha senyal de corona), lin' = S + E·(lin − S); si Y ≤ Ys, res;
  · r > R_EXT: lin' = S + E·(lin − S) a tots els píxels, exactament com l'e3 (idèntic bit a bit a la capa A anterior).
  Y = lin·YC i Ys = S·YC, amb la mateixa entrada, el mateix cel S i la mateixa fila Y del perfil de l'e3.
  Cap suavitzat, cap fos de vora, cap màscara nova: cada píxel decideix amb el seu propi valor.

Com: s'executa l'e3 TAL COM ÉS (runpy, sortides desviades a la carpeta de treball, com el v1), se'n comprova la reproducció
(JSON i vistes idèntics) i que la seva OUT és bit a bit la capa A anterior (OUT_rgb16.npy, SHA del V1_CORRECCIO.json); se
n'agafen l'entrada U, el cel i la fila Y, i es recalcula la capa amb la regla nova, per blocs de 512 files com l'e3.
Proves P1–P10 de la predeclaració, amb els criteris tal com hi són escrits.
Escriu (carpeta de treball): OUTB_rgb16_limbe.npy (la capa A nova i la fusionada). Dades del perfil del limbe per al gràfic:
resultats/v128_extincio_20261012/PERFIL_LIMBE_V128B.npz. Rebut: V1B_CORRECCIO_LIMBE.json.
Ús: PYTHONDONTWRITEBYTECODE=1 <python> v1b_correccio_limbe.py <carpeta_de_treball> [R_INT R_EXT]
    (els radis per defecte són els predeclarats; només es passen si la secció 5 de la predeclaració ho demana)"""
import hashlib
import json
import os
import runpy
import shutil
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

T0 = time.time()
AQUI = Path(__file__).resolve().parent
ARREL = AQUI.parents[2]                                                 # …/4-Photoshop
EXT = ARREL / '3-RECERCA/tools/extincio_diferencial_20261012'
RES = ARREL / '3-RECERCA/resultats/v128_extincio_20261012'
PRED = RES / 'PREDECLARACIO_LIMBE.md'
TREB = Path(sys.argv[1]).resolve()
TREB.mkdir(parents=True, exist_ok=True)
R_INT_PRED, R_EXT_PRED = 440.0, 470.0
R_INT = float(sys.argv[2]) if len(sys.argv) > 2 else R_INT_PRED
R_EXT = float(sys.argv[3]) if len(sys.argv) > 3 else R_EXT_PRED
LLINDAR_G = 0.002                         # P5/P6: Y − Ys > 0,002 per llegir el guany efectiu
TOL_P5 = 0.005                            # |Ĝ/E − 1| ≤ 0,5 %
TOL_P6 = 0.05                             # mediana de la fracció aplicada 1 ± 0,05
E_MIN_P6 = 0.02                           # sectors amb |E − 1| ≥ 0,02
assert PRED.is_file(), 'falta la predeclaració'
pred_sha = hashlib.sha256(PRED.read_bytes()).hexdigest()
pred_mtime = PRED.stat().st_mtime
assert pred_mtime < T0, 'la predeclaració ha de ser anterior al càlcul'

sys.path.insert(0, str(EXT))
import ed_comu as ed  # noqa: E402

# ------------------------------------------------------------------------------------------------ 0. la capa A anterior
v1 = json.load(open(RES / 'V1_CORRECCIO.json'))
OUT_VELL = np.load(TREB / 'OUT_rgb16.npy')
sha_vell = hashlib.sha256(np.ascontiguousarray(OUT_VELL).tobytes()).hexdigest()
assert sha_vell == v1['matriu']['sha256_bytes_OUT'], f'OUT_rgb16.npy no és la capa A anterior: {sha_vell}'

# ------------------------------------------------------------------------------------------------ 1. l'e3, tal com és
RES_ORIG, SORT_ORIG = ed.RES, ed.SORT
ed.RES = TREB / 'e3b_resultats'
ed.SORT = TREB / 'e3b_sortides'
ed.RES.mkdir(exist_ok=True)
ed.SORT.mkdir(exist_ok=True)
shutil.copy2(RES_ORIG / 'E1_MASSA_AIRE_FINAL.json', ed.RES / 'E1_MASSA_AIRE_FINAL.json')
e3 = EXT / 'e3_pis2_final_aproximacio.py'
print(f'== executo {e3.name} amb les sortides a {TREB}', flush=True)
G = runpy.run_path(str(e3), run_name='__main__')
U, OUT_E3, cel, YC, sp, g = G['U'], G['OUT'], G['cel'], G['YC'], G['sp'], G['g']
H, W = ed.HF, ed.WF
assert U.shape == (H, W, 3) and U.dtype == np.uint16
nou = json.load(open(ed.RES / 'E3_PIS2.json'))
vell = json.load(open(RES_ORIG / 'E3_PIS2.json'))
dif_json = []


def compara(a, b, cami=''):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if cami == '' and k in ('data', 'segons'):
                continue
            if k not in a or k not in b:
                dif_json.append(f'{cami}/{k}: falta')
            else:
                compara(a[k], b[k], f'{cami}/{k}')
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            compara(x, y, f'{cami}[{i}]')
    elif a != b:
        dif_json.append(f'{cami}: {a!r} != {b!r}')


compara(nou, vell)
vistes = {n: ed.sha256(ed.SORT / n) == ed.sha256(SORT_ORIG / n)
          for n in ('P2_A_final_tal_com_es.jpg', 'P2_B_final_amb_correccio_APROXIMACIO.jpg', 'P2_C_quocient.jpg',
                    'P2_costat_a_costat.jpg')}
e3_igual_capa_vella = bool(np.array_equal(OUT_E3, OUT_VELL))
assert not dif_json and all(vistes.values()) and e3_igual_capa_vella, (dif_json[:5], vistes, e3_igual_capa_vella)
del OUT_E3
G.pop('OUT', None)
print(f'e3 reproduït: JSON i vistes idèntics, OUT = capa A anterior bit a bit ({time.time() - T0:.0f} s)', flush=True)

# ------------------------------------------------------------------------------------------------ 2. la capa nova
LX, LY = ed.LLUNA_F
RL = ed.R_LLUNA_F
VZ = np.array(json.load(open(RES_ORIG / 'E1_MASSA_AIRE_FINAL.json'))['zenit']['vector_imatge_xfila'])
M = 500                                                     # finestra al voltant de la Lluna (R_EXT + 30 px)
assert R_EXT + 10 < M
wx0, wx1, wy0, wy1 = int(LX) - M, int(LX) + M + 1, int(LY) - M, int(LY) + M + 1
WIN = {k: np.zeros((wy1 - wy0, wx1 - wx0), np.float64) for k in ('Y', 'Ys', 'E', 'Yn', 'Yv')}
WIN['corr_n'] = np.zeros((wy1 - wy0, wx1 - wx0), bool)      # la capa nova hi aplica E
WIN['retall'] = np.zeros((wy1 - wy0, wx1 - wx0), bool)
OUTB = np.empty_like(U)
c = dict(p1_interior_diferents=0, p2_interior_amb_dada=0, p3_fosc_anell_diferents=0, p3_fosc_anell_n=0,
         p4_fora_diferents_de_la_vella=0, p4_fora_n=0, nul_formula_vs_entrada=0,
         canviats_vs_entrada=0, canvi_max_vs_entrada=0, canviats_vs_vella=0, canviats_vs_vella_fora_de_l_anell=0,
         canvi_max_vs_vella=0, anell_n=0, anell_amb_dada=0, anell_corregits_diferents_de_l_entrada=0,
         retall_alt=0, retall_baix=0, retall_alt_vell=0)
vell_fosc = dict(n=0, canviats_capa_vella=0, canviats_capa_nova=0, r=[], fora_de_l_anell=0)
p5 = dict(n=0, max_abs=0.0, sum_abs=0.0)
p5_list = []
p8 = dict(abans_RG=0.0, abans_BG=0.0)
p8_dRG, p8_dBG = [], []
nous_retalls = []
PAS = 512
cols = np.arange(W, dtype=np.float64)
for y0 in range(0, H, PAS):
    y1 = min(H, y0 + PAS)
    rows = np.arange(y0, y1, dtype=np.float64)
    XX, YY = np.meshgrid(cols, rows)
    u0 = U[y0:y1]
    v0 = OUT_VELL[y0:y1]
    lin = (u0.astype(np.float64) / 65535.0) ** ed.GAMMA
    S = cel(XX, YY)
    E = ed.factor_E(sp.X_graella(rows, cols), sp.X_sol)
    rl = np.hypot(XX - LX, YY - LY)
    Y = lin @ YC
    Ys = S @ YC
    dada = Y > Ys
    inter = rl < R_INT
    anell = (rl >= R_INT) & (rl <= R_EXT)
    fora = rl > R_EXT
    intacte = inter | (anell & ~dada)
    Ee = np.where(intacte, 1.0, E)
    cor = lin - S
    lin2 = S + Ee[..., None] * cor
    o = np.round(np.clip(lin2, 0.0, 1.0) ** (1.0 / ed.GAMMA) * 65535.0).astype(np.uint16)
    c['nul_formula_vs_entrada'] += int((np.any(o != u0, axis=2) & intacte).sum())   # control nul del camí amb E = 1
    o[intacte] = u0[intacte]                                                         # «res»: el valor de l'entrada, literal
    OUTB[y0:y1] = o
    lin2e = np.where(intacte[..., None], lin, lin2)
    ret = np.any(lin2e > 1.0, axis=2)
    c['retall_alt'] += int(ret.sum())
    c['retall_baix'] += int(np.any(lin2e < 0.0, axis=2).sum())
    lluna_e3 = rl <= RL
    lin2v = S + np.where(lluna_e3, 1.0, E)[..., None] * cor
    ret_v = np.any(lin2v > 1.0, axis=2)
    c['retall_alt_vell'] += int(ret_v.sum())
    for yy_, xx_ in zip(*np.nonzero(ret & ~ret_v)):
        nous_retalls.append(dict(x=int(xx_), y=int(y0 + yy_), r_lluna=round(float(rl[yy_, xx_]), 2)))
    do = np.any(o != u0, axis=2)
    dv = np.any(o != v0, axis=2)
    # P1–P4
    c['p1_interior_diferents'] += int((do & inter).sum())
    c['p2_interior_amb_dada'] += int((inter & dada).sum())
    c['p3_fosc_anell_n'] += int((anell & ~dada).sum())
    c['p3_fosc_anell_diferents'] += int((do & anell & ~dada).sum())
    c['p4_fora_n'] += int(fora.sum())
    c['p4_fora_diferents_de_la_vella'] += int((dv & fora).sum())
    vf = (rl > RL) & (rl <= RL + 20) & ~dada                                          # els 1.044 del v5 (mateixa definició)
    vell_fosc['n'] += int(vf.sum())
    vell_fosc['canviats_capa_vella'] += int((np.any(v0 != u0, axis=2) & vf).sum())
    vell_fosc['canviats_capa_nova'] += int((do & vf).sum())
    vell_fosc['fora_de_l_anell'] += int((vf & fora).sum())
    vell_fosc['r'] += rl[vf].tolist()
    # P9 i recomptes
    c['canviats_vs_entrada'] += int(do.sum())
    d = np.abs(o.astype(np.int32) - u0.astype(np.int32))
    c['canvi_max_vs_entrada'] = max(c['canvi_max_vs_entrada'], int(d.max()))
    c['canviats_vs_vella'] += int(dv.sum())
    c['canviats_vs_vella_fora_de_l_anell'] += int((dv & ~anell).sum())
    if dv.any():
        c['canvi_max_vs_vella'] = max(c['canvi_max_vs_vella'], int(np.abs(o.astype(np.int32) - v0.astype(np.int32))[dv].max()))
    c['anell_n'] += int(anell.sum())
    c['anell_amb_dada'] += int((anell & dada).sum())
    c['anell_corregits_diferents_de_l_entrada'] += int((do & anell & dada).sum())
    # P5: guany efectiu llegit de la sortida codificada
    lin_o = (o.astype(np.float64) / 65535.0) ** ed.GAMMA
    Yo = lin_o @ YC
    m5 = (rl >= R_INT) & ((Y - Ys) > LLINDAR_G) & ~ret & ~intacte
    if m5.any():
        q = (Yo[m5] - Ys[m5]) / (Y[m5] - Ys[m5]) / E[m5] - 1.0
        p5['n'] += int(m5.sum())
        p5['max_abs'] = max(p5['max_abs'], float(np.abs(q).max()))
        p5['sum_abs'] += float(np.abs(q).sum())
        ma = m5 & anell
        if ma.any():
            p5_list += ((Yo[ma] - Ys[ma]) / (Y[ma] - Ys[ma]) / E[ma] - 1.0).tolist()
    # P8: to de la part de corona (abans i després d'arrodonir), píxels de l'anell corregits
    ok = anell & dada & ~ret & (cor[..., 1] > 0.01)
    if ok.any():
        c2 = Ee[..., None] * cor
        p8['abans_RG'] = max(p8['abans_RG'], float(np.max(np.abs(c2[..., 0][ok] / c2[..., 1][ok] - cor[..., 0][ok] / cor[..., 1][ok]))))
        p8['abans_BG'] = max(p8['abans_BG'], float(np.max(np.abs(c2[..., 2][ok] / c2[..., 1][ok] - cor[..., 2][ok] / cor[..., 1][ok]))))
        co = lin_o - S
        p8_dRG += np.abs(co[..., 0][ok] / co[..., 1][ok] - cor[..., 0][ok] / cor[..., 1][ok]).tolist()
        p8_dBG += np.abs(co[..., 2][ok] / co[..., 1][ok] - cor[..., 2][ok] / cor[..., 1][ok]).tolist()
    # finestra per a P2 (connexió), P6 i el gràfic
    a0, a1 = max(y0, wy0), min(y1, wy1)
    if a0 < a1:
        sl = slice(a0 - y0, a1 - y0)
        ws = slice(a0 - wy0, a1 - wy0)
        lin_v = (v0[sl, wx0:wx1].astype(np.float64) / 65535.0) ** ed.GAMMA
        WIN['Y'][ws] = Y[sl, wx0:wx1]
        WIN['Ys'][ws] = Ys[sl, wx0:wx1]
        WIN['E'][ws] = E[sl, wx0:wx1]
        WIN['Yn'][ws] = Yo[sl, wx0:wx1]
        WIN['Yv'][ws] = lin_v @ YC
        WIN['corr_n'][ws] = ~intacte[sl, wx0:wx1]
        WIN['retall'][ws] = ret[sl, wx0:wx1] | ret_v[sl, wx0:wx1]
print(f'capa nova ({time.time() - T0:.0f} s): {json.dumps(c)}', flush=True)

# ------------------------------------------------------------------------------------------------ 3. proves a la finestra
wrows, wcols = np.arange(wy0, wy1, dtype=np.float64), np.arange(wx0, wx1, dtype=np.float64)
WX, WY = np.meshgrid(wcols, wrows)
rl = np.hypot(WX - LX, WY - LY)
ang = np.degrees(np.arctan2(WY - LY, WX - LX)) % 360.0          # 0 = +x (dreta), 90 = cap avall (com el v5)
dz = ((WX - LX) * VZ[0] + (WY - LY) * VZ[1]) / np.maximum(rl, 1e-9)
Yw, Ysw, Ew, Yn, Yv = WIN['Y'], WIN['Ys'], WIN['E'], WIN['Yn'], WIN['Yv']
dadaw = Yw > Ysw
corr_v = rl > RL                                                 # la capa anterior hi aplicava E

# P2: els píxels amb dada a r < R_INT, si n'hi ha: tocant l'anell (connectats) o aïllats
p2 = dict(n=c['p2_interior_amb_dada'])
if c['p2_interior_amb_dada']:
    lab, _ = nd.label(dadaw, structure=np.ones((3, 3), bool))
    toca = set(np.unique(lab[dadaw & (rl >= R_INT)]).tolist()) - {0}
    mi = dadaw & (rl < R_INT)
    toca_m = mi & np.isin(lab, list(toca))
    comp_aill = np.unique(lab[mi & ~toca_m])
    mides = nd.sum(np.ones_like(rl), lab, comp_aill) if len(comp_aill) else np.array([])
    p2.update(grups_aillats=int(len(comp_aill)), mida_dels_grups_px=[int(mides.min()), int(np.median(mides)), int(mides.max())]
              if len(mides) else None,
              Y_aillats=[float(Yw[mi & ~toca_m].min()), float(np.median(Yw[mi & ~toca_m])), float(Yw[mi & ~toca_m].max())]
              if (mi & ~toca_m).any() else None)
    p2.update(tocant_l_anell=int(toca_m.sum()), aillats=int((mi & ~toca_m).sum()),
              r_min_tocant=float(rl[toca_m].min()) if toca_m.any() else None,
              r_aillats=[float(rl[mi & ~toca_m].min()), float(rl[mi & ~toca_m].max())] if (mi & ~toca_m).any() else None,
              Y_menys_Ys_aillats_max=float((Yw - Ysw)[mi & ~toca_m].max()) if (mi & ~toca_m).any() else None,
              mostra=[dict(x=int(WX[i]), y=int(WY[i]), r=round(float(rl[i]), 2), Y=float(Yw[i]), Ys=float(Ysw[i]))
                      for i in zip(*np.nonzero(mi))][:50])
# nivell del disc (per al rebut): Y del disc i del cel
disc_in = rl < 430
nivell_disc = dict(Y_mediana_r_menys_430=float(np.median(Yw[disc_in])), Y_p99=float(np.percentile(Yw[disc_in], 99)),
                   Y_max=float(Yw[disc_in].max()), Ys_mediana=float(np.median(Ysw[disc_in])))

# P6a: parells de veïns (4-veïnatge) amb dada als dos costats i guanys diferents, capa nova i capa anterior
def parells(corr, Yout):
    """Parells de veïns (4-veïnatge, 430–480 px) on la capa aplica guanys diferents (un corregit, l'altre no): amb dada als
    dos costats (Y > Ys: el graó que la norma no permet) o a la vora de la dada (un costat sense dada: on la norma l'atura).
    Salt del quocient de lluminància (sortida / entrada) entre els dos."""
    out = dict(amb_dada_als_dos_costats=0, a_la_vora_de_la_dada=0)
    dq_dada, dq_vora = [], []
    q = Yout / np.maximum(Yw, 1e-12)
    for sa, sb in (((slice(None), slice(0, -1)), (slice(None), slice(1, None))), ((slice(0, -1), slice(None)), (slice(1, None), slice(None)))):
        dif = corr[sa] != corr[sb]
        zona = (rl[sa] >= 430) & (rl[sa] <= 480)
        ambdos = dif & dadaw[sa] & dadaw[sb] & zona
        vora = dif & ~(dadaw[sa] & dadaw[sb]) & zona
        out['amb_dada_als_dos_costats'] += int(ambdos.sum())
        out['a_la_vora_de_la_dada'] += int(vora.sum())
        dq_dada += np.abs(q[sa] - q[sb])[ambdos].tolist()
        dq_vora += np.abs(q[sa] - q[sb])[vora].tolist()
    for nom, l in (('salt_del_quocient_amb_dada', dq_dada), ('salt_del_quocient_a_la_vora', dq_vora)):
        out[nom] = dict(mediana=float(np.median(l)), p99=float(np.percentile(l, 99)), max=float(np.max(l))) if l else None
    return out


parells_nova = parells(WIN['corr_n'], Yn)
parells_vella = parells(corr_v, Yv)

# P6b: perfil per sectors de 10° a 430–480 px, cada 0,5 px
NB = 100
r0 = 430.0
rc = r0 + 0.5 * np.arange(NB) + 0.25
sector = np.floor(ang / 10.0).astype(int) % 36
rbin = np.floor((rl - r0) / 0.5).astype(int)
dins = (rbin >= 0) & (rbin < NB)
mg = dins & ((Yw - Ysw) > LLINDAR_G) & ~WIN['retall']
den = np.where(np.abs(Ew - 1) > 1e-9, Ew - 1, np.nan)
fr_n = ((Yn - Ysw) / np.maximum(Yw - Ysw, 1e-12) - 1.0) / den       # fracció de la correcció aplicada (1 = tota, 0 = gens)
fr_v = ((Yv - Ysw) / np.maximum(Yw - Ysw, 1e-12) - 1.0) / den
P = {k: np.full((36, NB), np.nan) for k in ('Y', 'Ys', 'Yn', 'Yv', 'frac_dada', 'fr_n', 'fr_v', 'n_g', 'qn', 'qv')}
E_sec = np.zeros(36)
for s in range(36):
    ii = np.nonzero((sector == s) & dins)
    E_sec[s] = float(np.median(Ew[ii]))
    rb_s = rbin[ii]
    sub = {k: v[ii] for k, v in (('Y', Yw), ('Ys', Ysw), ('Yn', Yn), ('Yv', Yv), ('dada', dadaw), ('mg', mg), ('fn', fr_n), ('fv', fr_v))}
    for k in range(NB):
        m = rb_s == k
        if not m.any():
            continue
        P['Y'][s, k], P['Ys'][s, k] = np.median(sub['Y'][m]), np.median(sub['Ys'][m])
        P['Yn'][s, k], P['Yv'][s, k] = np.median(sub['Yn'][m]), np.median(sub['Yv'][m])
        P['qn'][s, k], P['qv'][s, k] = np.median(sub['Yn'][m] / sub['Y'][m]), np.median(sub['Yv'][m] / sub['Y'][m])
        P['frac_dada'][s, k] = sub['dada'][m].mean()
        m2 = m & sub['mg']
        P['n_g'][s, k] = m2.sum()
        if m2.sum() >= 5 and abs(E_sec[s] - 1) >= E_MIN_P6:
            P['fr_n'][s, k] = np.median(sub['fn'][m2])
            P['fr_v'][s, k] = np.median(sub['fv'][m2])
# limbe real per sector (mateix criteri del v5: 50 % entre el disc, 420–440 px, i el pic de fora, 448–480 px)
r50 = np.full(36, np.nan)
for s in range(36):
    msec = (sector == s) & (rl >= 420) & (rl <= 480)
    rb_ = np.floor((rl[msec] - 420) / 0.5).astype(int)
    yv = Yw[msec]
    prof = np.array([np.median(yv[rb_ == k]) if (rb_ == k).any() else np.nan for k in range(120)])
    rcc = 420 + 0.5 * np.arange(120) + 0.25
    yin = np.nanmedian(prof[(rcc >= 420) & (rcc <= 440)])
    pk = np.nanmax(prof[(rcc >= 448) & (rcc <= 480)])
    thr = yin + 0.5 * (pk - yin)
    sobre = (rcc >= 440) & (prof >= thr)
    k0 = int(np.argmax(sobre))
    r50[s] = rcc[k0 - 1] + (thr - prof[k0 - 1]) / (prof[k0] - prof[k0 - 1]) * 0.5 if prof[k0] != prof[k0 - 1] else rcc[k0]
vora_dada = np.array([rc[np.argmax(P['frac_dada'][s] >= 0.5)] - 0.25 if (P['frac_dada'][s] >= 0.5).any() else np.nan
                      for s in range(36)])
valids = ~np.isnan(P['fr_n'])
fora_tol_n = valids & (np.abs(P['fr_n'] - 1) > TOL_P6)
fora_tol_v = valids & (np.abs(P['fr_v'] - 1) > TOL_P6)
sectors_E = [s for s in range(36) if abs(E_sec[s] - 1) >= E_MIN_P6]
# zenit i horitzó (±15° des del centre lunar), per al gràfic
PZH = {}
for nom, m0 in (('zenit', dz > np.cos(np.radians(15))), ('horitzo', dz < -np.cos(np.radians(15)))):
    pr = {k: np.full(NB, np.nan) for k in ('Y', 'Ys', 'Yn', 'Yv', 'qn', 'qv', 'E')}
    for k in range(NB):
        m = m0 & dins & (rbin == k)
        if m.any():
            for kk, arr in (('Y', Yw), ('Ys', Ysw), ('Yn', Yn), ('Yv', Yv), ('E', Ew)):
                pr[kk][k] = np.median(arr[m])
            pr['qn'][k], pr['qv'][k] = np.median(Yn[m] / Yw[m]), np.median(Yv[m] / Yw[m])
    PZH[nom] = pr
np.savez_compressed(RES / 'PERFIL_LIMBE_V128B.npz', rc=rc, E_sec=E_sec, r50=r50, vora_dada=vora_dada, R_INT=R_INT, R_EXT=R_EXT,
                    RL=RL, **{f'sec_{k}': v for k, v in P.items()}, **{f'{n}_{k}': v for n, pr in PZH.items() for k, v in pr.items()})

# ------------------------------------------------------------------------------------------------ 4. mosaic, balanç i desa
def mosaic(a):
    out = {}
    for ch in range(3):
        x = a[..., ch].astype(np.float64)
        out['RGB'[ch]] = dict(files=float(x[0::2].mean() - x[1::2].mean()), columnes=float(x[:, 0::2].mean() - x[:, 1::2].mean()),
                              diagonal=float(x[0::2, 0::2].mean() + x[1::2, 1::2].mean() - x[0::2, 1::2].mean() - x[1::2, 0::2].mean()))
    return out


mos = dict(entrada=mosaic(U[:H // 2 * 2, :W // 2 * 2]), capa_nova=mosaic(OUTB[:H // 2 * 2, :W // 2 * 2]))
bal = {}
for nom, a in (('entrada', U), ('capa_anterior', OUT_VELL), ('capa_nova', OUTB)):
    mm = a.reshape(-1, 3).astype(np.float64).mean(0)
    bal[nom] = dict(mitjana_16bits=mm.tolist(), R_G=float(mm[0] / mm[1]), B_G=float(mm[2] / mm[1]))
np.save(TREB / 'OUTB_rgb16_limbe.npy', OUTB)
sha_b = hashlib.sha256(np.ascontiguousarray(OUTB).tobytes()).hexdigest()
vf_r = np.array(vell_fosc.pop('r'))
vell_fosc.update(r_min_mediana_max=[round(float(vf_r.min()), 2), round(float(np.median(vf_r)), 2), round(float(vf_r.max()), 2)]
                 if len(vf_r) else None)
p5_arr = np.abs(np.array(p5_list))
proves = dict(
    P1_interior=dict(criteri=f'r < {R_INT:g} px: 0 píxels diferents de l\'entrada', diferents=c['p1_interior_diferents'],
                     passa=c['p1_interior_diferents'] == 0),
    P2_cap_corona_dins=dict(
        p2, criteri=f'píxels amb Y > Ys a r < {R_INT:g} px (s\'espera 0; si n\'hi ha, secció 5 de la predeclaració)',
        esperat_0_complert=c['p2_interior_amb_dada'] == 0,
        seccio_5=(None if c['p2_interior_amb_dada'] == 0 else
                  'b: tots aïllats dins del disc (no toquen l\'anell): són la Lluna de Pere; es diuen i es deixen intactes; la regla no '
                  'canvia' if p2.get('tocant_l_anell') == 0 else 'a: n\'hi ha que toquen l\'anell: cal baixar R_INT i tornar a calcular'),
        veredicte=('PASSA' if c['p2_interior_amb_dada'] == 0 else
                   'DECLARADA (secció 5b: aïllats dins del disc, intactes)' if p2.get('tocant_l_anell') == 0 else 'FALLA (secció 5a)'),
        passa=c['p2_interior_amb_dada'] == 0 or p2.get('tocant_l_anell') == 0),
    P3_fosc_intacte=dict(criteri='anell amb Y ≤ Ys: 0 diferents de l\'entrada; els foscos del v5 (453,64 < r ≤ 473,64 px, Y ≤ Ys): 0 canviats',
                         anell_fosc_n=c['p3_fosc_anell_n'], anell_fosc_diferents=c['p3_fosc_anell_diferents'], foscos_del_v5=vell_fosc,
                         passa=c['p3_fosc_anell_diferents'] == 0 and vell_fosc['canviats_capa_nova'] == 0),
    P4_fora_de_l_anell=dict(criteri=f'r > {R_EXT:g} px: 0 diferents de la capa A anterior', n=c['p4_fora_n'],
                            diferents=c['p4_fora_diferents_de_la_vella'], passa=c['p4_fora_diferents_de_la_vella'] == 0),
    P5_tota_la_corona_porta_E=dict(criteri=f'r ≥ {R_INT:g} px, Y − Ys > {LLINDAR_G}, sense retall: |Ĝ/E − 1| ≤ {TOL_P5}',
                                   n=p5['n'], max_abs=p5['max_abs'], mitjana_abs=p5['sum_abs'] / max(p5['n'], 1),
                                   anell=dict(n=int(len(p5_arr)), max_abs=float(p5_arr.max()) if len(p5_arr) else None,
                                              p99_abs=float(np.percentile(p5_arr, 99)) if len(p5_arr) else None),
                                   passa=p5['max_abs'] <= TOL_P5),
    P6_perfil_del_guany=dict(
        criteri=(f'36 sectors de 10°, 430–480 px cada 0,5 px; intervals amb ≥ 5 px de corona (Y − Ys > {LLINDAR_G}) en sectors amb '
                 f'|E − 1| ≥ {E_MIN_P6}: mediana de (Ĝ − 1)/(E − 1) = 1 ± {TOL_P6}; i 0 parells de veïns amb dada als dos costats '
                 'i guanys diferents'),
        sectors_avaluats=sectors_E, intervals_avaluats=int(valids.sum()),
        intervals_fora_de_tolerancia_capa_nova=int(fora_tol_n.sum()), intervals_fora_de_tolerancia_capa_anterior=int(fora_tol_v.sum()),
        fraccio_aplicada_capa_nova=dict(min=float(np.nanmin(P['fr_n'])), mediana=float(np.nanmedian(P['fr_n'])), max=float(np.nanmax(P['fr_n']))),
        fraccio_aplicada_capa_anterior=dict(min=float(np.nanmin(P['fr_v'])), mediana=float(np.nanmedian(P['fr_v'])), max=float(np.nanmax(P['fr_v']))),
        parells_capa_nova=parells_nova, parells_capa_anterior=parells_vella,
        limbe_real_px=[round(float(x), 2) for x in r50], vora_de_la_dada_px=[round(float(x), 2) for x in vora_dada],
        E_per_sector=[round(float(x), 4) for x in E_sec],
        passa=int(fora_tol_n.sum()) == 0 and parells_nova['amb_dada_als_dos_costats'] == 0),
    P7_retalls=dict(per_sobre_de_1=c['retall_alt'], per_sota_de_0=c['retall_baix'], capa_anterior=c['retall_alt_vell'],
                    nous_respecte_de_la_capa_anterior=len(nous_retalls), on=nous_retalls[:200]),
    P8_to=dict(abans_d_arrodonir=dict(max_dRG=p8['abans_RG'], max_dBG=p8['abans_BG']),
               despres_d_arrodonir=dict(n=len(p8_dRG), p99_dRG=float(np.percentile(p8_dRG, 99)) if p8_dRG else None,
                                         max_dRG=float(np.max(p8_dRG)) if p8_dRG else None,
                                         p99_dBG=float(np.percentile(p8_dBG, 99)) if p8_dBG else None,
                                         max_dBG=float(np.max(p8_dBG)) if p8_dBG else None),
               passa=max(p8['abans_RG'], p8['abans_BG']) < 1e-12),
    P9_canvis_respecte_de_la_capa_anterior=dict(px=c['canviats_vs_vella'], fora_de_l_anell=c['canviats_vs_vella_fora_de_l_anell'],
                                                max_DN16=c['canvi_max_vs_vella'], passa=c['canviats_vs_vella_fora_de_l_anell'] == 0),
    P10_mosaic_i_balanc=dict(mosaic_2x2_DN16=mos, balanc_per_canal_tot_el_llenc=bal),
    control_nul=dict(criteri='píxels intactes: el camí de la fórmula amb E = 1 dona el mateix que l\'entrada',
                     diferents=c['nul_formula_vs_entrada']))
info = dict(
    guio=ed.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    predeclaracio=dict(fitxer=ed.rel(PRED), sha256=pred_sha, modificada=time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(pred_mtime)),
                       anterior_al_calcul=True),
    regla=dict(R_INT=R_INT, R_EXT=R_EXT, adaptada=(R_INT, R_EXT) != (R_INT_PRED, R_EXT_PRED),
               centre_lluna=[LX, LY], cercle_e3=RL,
               text='r < R_INT: intacte; R_INT ≤ r ≤ R_EXT: E si Y > Ys, intacte si Y ≤ Ys; r > R_EXT: E (com l\'e3)'),
    e3=dict(guio=ed.rel(e3), sha256=ed.sha256(e3), E3_PIS2_identic=not dif_json, vistes_identiques=vistes,
            OUT_igual_a_la_capa_A_anterior=e3_igual_capa_vella),
    capa_anterior=dict(fitxer='OUT_rgb16.npy (carpeta de treball)', sha256_bytes=sha_vell),
    matriu=dict(forma=list(OUTB.shape), tipus='uint16', sha256_bytes_OUTB=sha_b,
                pixels_canviats_vs_entrada=c['canviats_vs_entrada'], fraccio=c['canviats_vs_entrada'] / (H * W),
                canvi_max_vs_entrada_DN16=c['canvi_max_vs_entrada'],
                anell=dict(n=c['anell_n'], amb_dada=c['anell_amb_dada'], sense_dada=c['p3_fosc_anell_n'],
                           corregits_que_canvien=c['anell_corregits_diferents_de_l_entrada'])),
    nivell_del_disc=nivell_disc, proves=proves,
    veredicte='PASSA' if all(v.get('passa', True) for v in proves.values()) else 'FALLA',
    segons=round(time.time() - T0, 1))
ed.json_dump(info, RES / 'V1B_CORRECCIO_LIMBE.json')
print(json.dumps({k: info[k] for k in ('regla', 'matriu', 'nivell_del_disc', 'veredicte')}, indent=1, ensure_ascii=False, default=str))
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ('on', 'mostra', 'limbe_real_px', 'vora_de_la_dada_px', 'E_per_sector')}
                  for k, v in proves.items() if k != 'P10_mosaic_i_balanc'}, indent=1, ensure_ascii=False, default=str))
print(f'fet ({time.time() - T0:.0f} s)')

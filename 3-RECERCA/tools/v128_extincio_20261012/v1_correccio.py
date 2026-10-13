"""v1 · La imatge corregida de la V128, a resolució plena i en 16 bits, amb EXACTAMENT el codi de l'e3 (12-10-2026).

No es copia ni es toca la recepta: s'executa `extincio_diferencial_20261012/e3_pis2_final_aproximacio.py` tal com és, amb
les seves sortides (vistes P2_* i E3_PIS2.json) desviades a una carpeta de treball, i se n'agafa la matriu OUT que calcula.
Mateix cel (polinomi de grau 2, blocs de 8, r ≥ 6 R☉, retall +2,5σ/−4σ, 6 rondes), mateix k = 0,40, mateix X☉, mateix
disc lunar intacte, mateixa codificació (563/256, 16 bits).

Proves de reproducció (el que Pere ha vist ha de ser el que va al PSB):
  · el E3_PIS2.json nou ha de ser idèntic a l'original, camp a camp (menys la data i els segons);
  · les vistes P2_A / P2_B / P2_C / P2_costat_a_costat noves han de ser idèntiques byte a byte a les de Sortides/;
  · i, sobre la matriu de 16 bits: control nul, disc lunar, on E = 1, R/G i B/G de la corona, retallats (ho fa l'e3), més
    el mosaic 2×2 i el balanç per canal (abans/després).
Escriu (carpeta de treball, fora del projecte): OUT_rgb16.npy (la capa i la fusionada de la V128), E_u16.npy (E/2 en 16 bits,
per a la capa de referència), U_alfa16.npy no (l'alfa de la fusionada es copia en cru al v2).
Rebut: resultats/v128_extincio_20261012/V1_CORRECCIO.json.
Ús: PYTHONDONTWRITEBYTECODE=1 <python> v1_correccio.py <carpeta_de_treball>"""
import hashlib
import json
import os
import runpy
import shutil
import sys
import time
from pathlib import Path

import numpy as np

T0 = time.time()
AQUI = Path(__file__).resolve().parent
ARREL = AQUI.parents[2]                                                 # …/4-Photoshop
EXT = ARREL / '3-RECERCA/tools/extincio_diferencial_20261012'
RES = ARREL / '3-RECERCA/resultats/v128_extincio_20261012'
TREB = Path(sys.argv[1]).resolve()
TREB.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(EXT))
import ed_comu as ed  # noqa: E402

RES_ORIG, SORT_ORIG = ed.RES, ed.SORT
ed.RES = TREB / 'e3_resultats'
ed.SORT = TREB / 'e3_sortides'
ed.RES.mkdir(exist_ok=True)
ed.SORT.mkdir(exist_ok=True)
shutil.copy2(RES_ORIG / 'E1_MASSA_AIRE_FINAL.json', ed.RES / 'E1_MASSA_AIRE_FINAL.json')   # entrada de l'e3 (només lectura)

e3 = EXT / 'e3_pis2_final_aproximacio.py'
print(f'== executo {e3.name} amb les sortides a {TREB}', flush=True)
G = runpy.run_path(str(e3), run_name='__main__')
U, OUT, icc = G['U'], G['OUT'], G['icc']
H, W = ed.HF, ed.WF
assert U.shape == OUT.shape == (H, W, 3) and OUT.dtype == np.uint16


def sha_fitxer(p):
    return ed.sha256(p)


# ------------------------------------------------------------------------------------------------ 1. reproducció
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
vistes = {}
for n in ('P2_A_final_tal_com_es.jpg', 'P2_B_final_amb_correccio_APROXIMACIO.jpg', 'P2_C_quocient.jpg', 'P2_costat_a_costat.jpg'):
    a, b = sha_fitxer(ed.SORT / n), sha_fitxer(SORT_ORIG / n)
    vistes[n] = dict(sha_nova=a, sha_de_la_que_va_veure_Pere=b, identica=a == b)
print('E3_PIS2.json: diferències', dif_json[:10], '| vistes idèntiques:', {k: v['identica'] for k, v in vistes.items()}, flush=True)

# ------------------------------------------------------------------------------------------------ 2. proves de la matriu
sp, g = G['sp'], G['g']
lluna_n = 0
canviats = 0
canvi_max = 0
E_u16 = np.empty((H, W), np.uint16)
PAS = 512
cols = np.arange(W, dtype=np.float64)
Emin, Emax = np.inf, -np.inf
for y0 in range(0, H, PAS):
    y1 = min(H, y0 + PAS)
    rows = np.arange(y0, y1, dtype=np.float64)
    E = ed.factor_E(sp.X_graella(rows, cols), sp.X_sol)
    Emin, Emax = min(Emin, float(E.min())), max(Emax, float(E.max()))
    E_u16[y0:y1] = np.round(np.clip(E / 2.0, 0, 1) * 65535.0).astype(np.uint16)
    XX, YY = np.meshgrid(cols, rows)
    ll = np.hypot(XX - ed.LLUNA_F[0], YY - ed.LLUNA_F[1]) <= ed.R_LLUNA_F
    lluna_n += int(ll.sum())
    d = np.abs(OUT[y0:y1].astype(np.int32) - U[y0:y1].astype(np.int32))
    canviats += int(np.any(d > 0, axis=2).sum())
    canvi_max = max(canvi_max, int(d.max()))


def mosaic(a):
    """Patró 2×2 (el del mosaic RGGB): diferència mitjana files parells − senars i columnes parells − senars, per canal,
    en nivells de 16 bits, i el seu quocient amb el gra (desviació de la diferència entre veïns)."""
    out = {}
    for c in range(3):
        x = a[..., c].astype(np.float64)
        f = float(x[0::2].mean() - x[1::2].mean())
        k = float(x[:, 0::2].mean() - x[:, 1::2].mean())
        diag = float(x[0::2, 0::2].mean() + x[1::2, 1::2].mean() - x[0::2, 1::2].mean() - x[1::2, 0::2].mean())
        out['RGB'[c]] = dict(files=f, columnes=k, diagonal=diag)
    return out


mos = dict(abans=mosaic(U[:H // 2 * 2, :W // 2 * 2]), despres=mosaic(OUT[:H // 2 * 2, :W // 2 * 2]))
bal = {}
for nom, a in (('abans', U), ('despres', OUT)):
    m = a.reshape(-1, 3).astype(np.float64).mean(0)
    bal[nom] = dict(mitjana_16bits=m.tolist(), R_G=float(m[0] / m[1]), B_G=float(m[2] / m[1]))
print(f'píxels canviats {canviats} ({100 * canviats / (H * W):.1f} %), canvi màxim {canvi_max} DN16; E {Emin:.4f}–{Emax:.4f}', flush=True)

# ------------------------------------------------------------------------------------------------ 3. desa
np.save(TREB / 'OUT_rgb16.npy', OUT)
np.save(TREB / 'E_u16.npy', E_u16)
sha_out = hashlib.sha256(np.ascontiguousarray(OUT).tobytes()).hexdigest()
sha_E = hashlib.sha256(np.ascontiguousarray(E_u16).tobytes()).hexdigest()
sha_U = hashlib.sha256(np.ascontiguousarray(U).tobytes()).hexdigest()
info = dict(
    guio=ed.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    metode=('s\'executa l\'e3 sense cap canvi (runpy) amb les sortides desviades a la carpeta de treball; la matriu OUT és la '
            'capa i la fusionada de la V128'),
    e3=dict(guio=ed.rel(e3), sha256=sha_fitxer(e3), ed_comu_sha256=sha_fitxer(EXT / 'ed_comu.py')),
    entrada=dict(psb=ed.rel(ed.PSB), sha256=nou['entrada']['sha256'], perfil=nou['entrada']['perfil']['desc'],
                 perfil_sha256=nou['entrada']['perfil']['sha256']),
    reproduccio=dict(E3_PIS2_identic_menys_data_i_segons=not dif_json, diferencies=dif_json[:50], vistes=vistes),
    proves_e3=nou['proves'], recepta=nou['recepta'],
    matriu=dict(forma=list(OUT.shape), tipus='uint16', sha256_bytes_OUT=sha_out, sha256_bytes_U=sha_U,
                pixels_canviats=canviats, fraccio_canviada=canviats / (H * W), canvi_max_DN16=canvi_max,
                disc_lunar_px=lluna_n, E_min=Emin, E_max=Emax,
                E_u16=dict(codificacio='valor = E/2 (gris del 50 % = E 1)', sha256_bytes=sha_E),
                mosaic_2x2_DN16=mos, balanc_per_canal_tot_el_llenc=bal),
    segons=round(time.time() - T0, 1))
ed.json_dump(info, RES / 'V1_CORRECCIO.json')
print(json.dumps({k: info[k] for k in ('reproduccio', 'matriu')}, indent=1, ensure_ascii=False, default=str)[:4000])
print(f'fet ({time.time() - T0:.0f} s)')

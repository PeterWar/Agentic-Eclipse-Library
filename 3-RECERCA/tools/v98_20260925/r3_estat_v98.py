"""r3 (V98) · L'«estat V98» per al jutge i per al PSB: el de la V97 (estat_v97, clons APFS) amb NOMÉS aquests canvis:
  · els 16 filtres (41–56): ràster i alfa nous (f3_filtres_v98.py, sobre la linealitzada V98 amb la franja neta A3B);
  · les màscares de Pere d'aquests 16 filtres: a ZERO dins del disc de presentació de la Lluna on la Lluna de Pere hi és opaca, com demana
    Pere al punt 1 («a la part esquerra de la Lluna no hi quedi cap píxel ni en el filtre ni en les màscares»; l'excepció de la dreta és un
    permís, i dins del disc tampoc no hi ha res a mostrar: la dada de la dreta de dins del disc és la cromosfera de prop de C3). Fora del disc,
    les màscares són les de Pere byte a byte. Les originals queden a estat_v97 i a la V97.psb;
  · EXCEPCIÓ, la VORA TRANSLÚCIDA de la Lluna de Pere (capa 258 amb alfa < 0,99 dins del cercle): només passa a dalt i a baix
    (1–3 px; a l'esquerra, 150–210°, la Lluna hi és opaca, 0,993, i a la dreta també). Allà, sota la Lluna translúcida, les capes en
    Multiplicar (41–46) hi continuen el NIVELL de l'arc (el valor a 0 ≤ d < 1 del mateix azimut), amb la màscara de Pere: sense això, la
    base sense filtrar s'hi veu i fa una línia clara concèntrica al limbe (compost emulat de la 1a iteració de la V98). Les capes en
    Superposar hi són transparents (neutres);
  · la base (3): la de la fusió nova (b3 sense el residu local A→B, que feia el graó diagonal) amb la recepta de la V97 i la base de la V96
    arran del limbe (f2b + f2c), si es dona <base_u16.npy>; si no, la de la V97;
  · totes les altres capes, les de la V97.
Ús: r3_estat_v98.py <filtres_dir> <sortida> [<base_u16.npy>]"""
import sys, json, subprocess
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; REF = ARREL / '4-RESULTATS/v97_refundacio_20260924/estat_v97'
FIL, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native',
       47: '03', 48: '03v30', 49: '07', 50: '01', 51: '04', 52: '05', 53: '06', 54: 'P03_MGN', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; H, W = 7506, 10551
def clona(src, dst):
    if dst.exists(): dst.unlink()
    subprocess.run(['cp', '-c', str(src), str(dst)], check=True)
meta = json.loads((REF / 'CAPES_V97.json').read_text()); nous = {}
BASE = Path(sys.argv[3]) if len(sys.argv) > 3 else None
for f in REF.glob('L*.npy'):
    lid = int(f.name[1:].split('_')[0])
    if lid in TAG or (lid == 3 and f.name == 'L3_RGB.npy' and BASE is not None): continue
    clona(f, OUT / f.name)
if BASE is not None: clona(BASE, OUT / 'L3_RGB.npy'); nous_base = str(BASE)
# el disc de presentació (rampa d'1 px a la vora): factor de màscara
y0, y1, x0, x1 = 3200, 4360, 4800, 5960; yy, xx = np.mgrid[y0:y1, x0:x1]; dL = np.hypot(xx - LX, yy - LY) - RL; fac = np.clip(dL, 0, 1).astype(np.float32)
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); from jutge_comu import Estat
a258 = Estat(REF).alfa_efectiva(258, (x0, y0, x1, y1)); transl = (dL < 0) & (a258 < 0.99)
thg = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
transl &= ~((thg >= 150) & (thg < 210))                            # a l'esquerra (150–210°) la Lluna hi és opaca (≥ 0,98): cap excepció, tal com demana Pere
opac = (dL < 0) & ~transl                                         # dins del cercle i la Lluna de Pere opaca: aquí, CAP píxel ni de filtre ni de màscara
fac = np.where(opac, 0.0, 1.0).astype(np.float32)                 # 2a iteració: sense rampa a 0 ≤ d < 1 (hi feia una línia clara: la base sense filtrar)
thb = ((np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360 * 4).astype(int) % 1440
MULT = (41, 42, 43, 44, 45, 46)
rep = {}
for lid, tag in TAG.items():
    u = FIL / f'{tag}_u16.npy'; assert u.exists(), (lid, tag)
    clona(u, OUT / f'L{lid}_G.npy'); clona(FIL / f'{tag}_alfa_u16.npy', OUT / f'L{lid}_alfa.npy'); nous[lid] = str(u)
    M = np.array(np.load(REF / f'L{lid}_mascara.npy')); sub = M[y0:y1, x0:x1].astype(np.float32); abans = int((sub[dL < 0] > 0).sum())
    M[y0:y1, x0:x1] = np.round(sub * fac).astype(np.uint16); np.save(OUT / f'L{lid}_mascara.npy', M)
    if lid in MULT:   # nivell de l'arc sota la vora translúcida de la Lluna: el valor del mateix azimut a 0 ≤ d < 1 (mediana per calaix de 0,25°)
        Gm = np.array(np.load(OUT / f'L{lid}_G.npy')); Am = np.array(np.load(OUT / f'L{lid}_alfa.npy')); gs = Gm[y0:y1, x0:x1].astype(np.float32)
        z = (dL >= 0) & (dL < 1); acc = np.bincount(thb[z], weights=gs[z], minlength=1440); nn = np.bincount(thb[z], minlength=1440)
        lev = np.where(nn > 0, acc / np.maximum(nn, 1), np.nan); okl = np.isfinite(lev); lev = np.interp(np.arange(1440), np.flatnonzero(okl), lev[okl], period=1440)
        gs = np.where(transl, lev[thb], gs); Gm[y0:y1, x0:x1] = np.round(gs).astype(np.uint16); Am[y0:y1, x0:x1] = np.where(opac, 0, 65535)   # Multiplicar: plena fora d'on la Lluna és opaca
        (OUT / f'L{lid}_G.npy').unlink(); (OUT / f'L{lid}_alfa.npy').unlink(); np.save(OUT / f'L{lid}_G.npy', Gm); np.save(OUT / f'L{lid}_alfa.npy', Am); del Gm, Am
    al = np.load(OUT / f'L{lid}_alfa.npy', mmap_mode='r')[y0:y1, x0:x1]
    rep[lid] = dict(mascara_px_dins_disc_abans=abans, mascara_px_on_la_lluna_es_opaca=int((M[y0:y1, x0:x1][opac] > 0).sum()), alfa_px_on_la_lluna_es_opaca=int((al[opac] > 0).sum()),
                    px_vora_translucida=int(transl.sum()), alfa_px_vora_translucida=int((al[transl] > 0).sum()), mascara_px_esquerra_150_210_dins_disc=int((M[y0:y1, x0:x1][(dL < 0) & (thb >= 600) & (thb < 840)] > 0).sum()))
    print(lid, rep[lid], flush=True)
meta['font'] = 'estat V98 (r3_estat_v98): filtres nous (f3 V98) i màscares dels filtres a zero dins del disc; la resta, V97'; meta['nous'] = {str(k): v for k, v in nous.items()}
if BASE is not None: meta['nous']['3'] = str(BASE)
meta['v98_mascares_disc'] = {str(k): v for k, v in rep.items()}; meta['v98_vora_translucida_px'] = int(transl.sum())
(OUT / 'CAPES_V98.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n'); print('FET', len(nous), 'capes noves')

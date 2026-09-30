"""c0 (V108, cadena) · La capa 56 (P05 WOW bilateral) amb la cura de la filera de punts de la V105 (REC: l'entrada de la 56 promitjada segons el
S/N a la franja de banda), com c0_estat_v105.py, perquè la cadena reprodueixi la 56 que hi ha a la V107:
  · pes 1 a d < 30 px de la Lluna de presentació, fosa smoothstep fins a 40 px; més enllà, la 56 de la cadena tal qual;
  · la fosa es fa sobre q(56) (la 56 amb la quantització del Photoshop), exactament com la V105, que va partir del canal REAL de la V104
    (= q de la 56 de l'estat): així la V107 es reprodueix BYTE A BYTE (verificat el 26-09: q(resultat) = canal 56 de la V107).
La REC es va calcular amb la linealitzada E (V104). Si la cadena corre amb unes altres fonts o una altra 56 i la 56 nova difereix de la d'E
a d < 60 px més de V108_FILA56_TOL LSB (per defecte 32 = 0,05 %), la REC ja no hi correspon: ATURA (exit 7) i cal regenerar-la
(3-RECERCA/tools/v105_limbe_20260926/fila/reprodueix_REC.sh) o posar V108_FILA56=cap (la 56 de la cadena sense la cura de la filera).
Ús: c0_fila56_v108.py <estat> <carpeta REC amb L56_G_moon.npy | cap>. Idempotent: la 56 de l'r3 queda a L56_G_r3.npy."""
import sys, os, json, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_v108 import ARREL, LLUNA, CAIXA_LLUNA, q_blocs, sha, rel, claim
claim()
EST = Path(sys.argv[1]); REC = sys.argv[2]; TOL = int(os.environ.get('V108_FILA56_TOL', '32')); t0 = time.time()
REF_E = ARREL / '4-RESULTATS/v103_banda_20260926/E/estat_v103/L56_G.npy'      # la 56 de l'r3 de la variant E (entrada de la REC)
src = EST / 'L56_G_r3.npy'; dst = EST / 'L56_G.npy'
if not src.exists(): os.replace(dst, src)
a3 = np.load(src); cx, cy, R = LLUNA; x0, y0, x1, y1 = CAIXA_LLUNA
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; t = np.clip((40 - d) / 10, 0, 1); w = t * t * (3 - 2 * t)
e = np.load(REF_E, mmap_mode='r')[y0:y1, x0:x1].astype(np.int32); dif = np.abs(a3[y0:y1, x0:x1].astype(np.int32) - e)
z = d < 60; rep = dict(estat=rel(EST), rec=REC if REC == 'cap' else rel(REC), tol_lsb=TOL, font_r3=rel(src), sha_r3=sha(src),
                       dif_56_contra_E_d_menys_60=dict(px=int((dif[z] > 0).sum()), max=int(dif[z].max()), p99=float(np.percentile(dif[z], 99))),
                       dif_56_contra_E_tot=dict(px=int((np.load(REF_E, mmap_mode='r') != a3).sum())))
if REC == 'cap':
    np.save(dst, a3); rep['canvi'] = 'cap: la 56 de la cadena tal qual (sense la cura de la filera de punts)'
else:
    if rep['dif_56_contra_E_d_menys_60']['max'] > TOL:
        print(f"ATURAT: la 56 nova difereix de la d'E a d < 60 px fins a {rep['dif_56_contra_E_d_menys_60']['max']} LSB (> {TOL}): la REC ({REC}) es va "
              "calcular amb la linealitzada E i ja no hi correspon. Regenera-la o posa V108_FILA56=cap.", flush=True); sys.exit(7)
    r = np.load(Path(REC) / 'L56_G_moon.npy').astype(np.float64); assert r.shape == (y1 - y0, x1 - x0), r.shape
    a = q_blocs(a3); v = a[y0:y1, x0:x1].astype(np.float64); n = np.rint(v + w * (r - v)).astype(np.uint16); a[y0:y1, x0:x1] = n
    np.save(dst, a); dd = np.abs(n.astype(np.int32) - v.astype(np.int32))
    rep['canvi'] = 'q(56) fos amb la REC a d < 40 px (pes 1 a d < 30, smoothstep 30–40), com la V105'
    rep['px_canviats_per_la_fosa'] = int((dd > 0).sum()); rep['dif_max_fosa'] = int(dd.max()); rep['dif_max_fosa_d_mes_40'] = int(dd[d >= 40].max())
    rep['sha_rec'] = sha(Path(REC) / 'L56_G_moon.npy')
rep['sha_L56_G'] = sha(dst); rep['segons'] = round(time.time() - t0, 1)
(EST / 'FILA56.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print(json.dumps(rep, ensure_ascii=False))

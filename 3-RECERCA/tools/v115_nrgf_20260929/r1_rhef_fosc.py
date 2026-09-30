"""r1 (V115, 29-09-2026) · RHEF local (45: 60°, 46: 30°) amb el COSTAT FOSC limitat. L'operador RHEF «mass» (V112, v112_20260928/rhef_mass.py) no canvia:
el seu resultat és el rang u ∈ [0, 1] de cada píxel dins del sector; aquí s'hi afegeix, al final de l'operador, el limitador del costat fosc:
    u' = ½ − k·(½ − u)  on u < ½   (u ≥ ½, igual)
Per què (4-RESULTATS/v114_artefactes_foscos_20260929/RESULTAT.md i la descomposició a3): una equalització per rang posa a negre el píxel més fosc
del sector per poc que ho sigui; al cel exterior, on la diferència real és de dècimes de %, crea els carrers foscos que Pere marca (1, 3, 4) i
fa la clotada més gran de les marques 7 i 8 (−4,3 i −4,9 punts de la 46). El limitador només treu enfosquiment (en Multiplicar, u' ≥ u vol dir
factor ≥), mai no posa llum per sobre de la base, i és global (cap porta radial ni de marca).
Ús: r1_rhef_fosc.py <carpeta_sortida> <k> [45|46 …]   (llegeix la cadena v114c: filtres_mass/filtres; l'alfa és la mateixa, clon APFS)"""
import sys, json, subprocess, hashlib, numpy as np
from pathlib import Path
R = Path(__file__).resolve().parents[3]
assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V115_NRGF_CLOTADES_20260929'
CT = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c/filtres_mass/filtres'
out = Path(sys.argv[1]); k = float(sys.argv[2]); capes = [int(x) for x in sys.argv[3:]] or [46]
TAG = {45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native'}
out.mkdir(parents=True, exist_ok=True); rep = dict(k=k, formula="u' = 1/2 - k (1/2 - u) on u < 1/2", font=str(CT.relative_to(R)), capes={})
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
for lid in capes:
    t = TAG[lid]; u = np.load(CT / f'{t}_u16.npy')
    uf = u.astype(np.float32) / 65535; v = np.where(uf < 0.5, 0.5 - k * (0.5 - uf), uf)
    u2 = np.round(np.clip(v, 0, 1) * 65535).astype(np.uint16); np.save(out / f'{t}_u16.npy', u2)
    fa = out / f'{t}_alfa_u16.npy'
    if not fa.exists(): subprocess.run(['cp', '-c', str(CT / f'{t}_alfa_u16.npy'), str(fa)], check=True)
    rep['capes'][str(lid)] = dict(tag=t, sha256_font=sha(CT / f'{t}_u16.npy'), sha256=sha(out / f'{t}_u16.npy'), px_canviats=int((u2 != u).sum()),
                                  frac_u_sota_mig=float((uf < 0.5).mean()), mitjana_abans=float(uf.mean()), mitjana_despres=float(v.mean()))
(out / 'R1_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False))

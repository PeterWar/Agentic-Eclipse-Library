"""r2_v120 (V120, 29-09): còpia de v115/r2_rhef_fosc_local.py amb el claim de la V120 i la carpeta d'entrada com a 5è argument opcional (--font <filtres_mass/filtres>; per defecte, la de la v114c).
r2 (V115, 29-09-2026) · RHEF local (45, 46) amb el COSTAT FOSC limitat i el NIVELL de gran escala conservat.
r1 (u' = ½ − k(½ − u) on u < ½) treia els carrers foscos però aixecava tot el camp (la meitat dels píxels de cada sector): +3 % de mitjana amb la 46
i, a través del genoll de la NRGF, un canvi de gradient de ±6–35 % (vista V115_canvi del primer intent, retirat). Aquí, després del limitador, es torna
el nivell mitjà de gran escala al de l'operador original:
    u'  = ½ − k·(½ − u)  on u < ½
    u'' = u' − G_σ(u' − u)      (G_σ = mitjana gaussiana normalitzada al domini de la capa, σ = S px)
Així el que canvia és el contrast LOCAL dels buits respecte del seu voltant (escales < σ); el to de gran escala del camp és el de la V114.
No afegeix ni treu mostres: és la corba de resposta de l'operador. Ús: r2_rhef_fosc_local.py <sortida> <k> <σ_px> [45|46 …]"""
import sys, json, subprocess, hashlib, numpy as np, cv2
from pathlib import Path
R = Path(__file__).resolve().parents[3]
# 30-09-2026: regla de l'escriptor únic retirada per Pere: assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V120_DISTORSIO_20260929'
CT = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c/filtres_mass/filtres'
if '--font' in sys.argv: i_ = sys.argv.index('--font'); CT = Path(sys.argv[i_ + 1]).resolve(); del sys.argv[i_:i_ + 2]
out = Path(sys.argv[1]); k = float(sys.argv[2]); S = float(sys.argv[3]); capes = [int(x) for x in sys.argv[4:]] or [45, 46]
TAG = {45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native'}
out.mkdir(parents=True, exist_ok=True); rep = dict(k=k, sigma_px=S, formula="u' = 1/2 - k(1/2 - u) on u<1/2; u'' = u' - G_sigma(u' - u)", font=str(CT.relative_to(R)), capes={})
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def gauss_dom(x, dom, s):
    """mitjana gaussiana normalitzada al domini, a 1/8 (camps suaus) i tornada a la mida original (bilineal)."""
    f = 8; h, w = x.shape; hs, ws = (h + f - 1) // f, (w + f - 1) // f
    xs = cv2.resize(np.where(dom, x, 0).astype(np.float32), (ws, hs), interpolation=cv2.INTER_AREA); ds = cv2.resize(dom.astype(np.float32), (ws, hs), interpolation=cv2.INTER_AREA)
    num = cv2.GaussianBlur(xs, (0, 0), s / f); den = cv2.GaussianBlur(ds, (0, 0), s / f)
    return cv2.resize(num / np.maximum(den, 1e-6), (w, h), interpolation=cv2.INTER_LINEAR)
for lid in capes:
    t = TAG[lid]; u = np.load(CT / f'{t}_u16.npy').astype(np.float32) / 65535; al = np.load(CT / f'{t}_alfa_u16.npy', mmap_mode='r')
    dom = np.asarray(al) > 0
    v = np.where(u < 0.5, 0.5 - k * (0.5 - u), u); d = v - u
    v2 = np.where(dom, v - gauss_dom(d, dom, S), u)
    u2 = np.round(np.clip(v2, 0, 1) * 65535).astype(np.uint16); np.save(out / f'{t}_u16.npy', u2)
    fa = out / f'{t}_alfa_u16.npy'
    if not fa.exists(): subprocess.run(['cp', '-c', str(CT / f'{t}_alfa_u16.npy'), str(fa)], check=True)
    rep['capes'][str(lid)] = dict(tag=t, sha256_font=sha(CT / f'{t}_u16.npy'), sha256=sha(out / f'{t}_u16.npy'), mitjana_abans=float(u[dom].mean()), mitjana_despres=float(v2[dom].mean()),
                                  canvi_p1_p99=[float(np.percentile((v2 - u)[dom], q)) for q in (1, 99)])
(out / 'R2_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False)[:600])

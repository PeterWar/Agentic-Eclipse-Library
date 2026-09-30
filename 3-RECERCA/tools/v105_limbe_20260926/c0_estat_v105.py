"""c0 (V105) · Estat de la V105 per al jutge i per al muntatge: el de la V104 (4-RESULTATS/v103_banda_20260926/E/estat_v103, per enllaços) amb
la 56 (WOW bilateral) de la cura de la filera de punts (REC: la resolució segueix el S/N a l'entrada, a la franja de banda,
conservant el perfil radial; agent «fila», 26-09) només arran del limbe: pes 1 a d < 30 px, fosa a 0 fins a 40 px; més enllà, la V104 exacta.
Ús: c0_estat_v105.py (escriu 4-RESULTATS/v105_limbe_20260926/claude/estat_v105)"""
import json, shutil, numpy as np
from pathlib import Path
R0 = Path(__file__).resolve().parents[3]
SRC = R0 / '4-RESULTATS/v103_banda_20260926/E/estat_v103'; DST = R0 / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'; REC = R0 / '4-RESULTATS/v105_limbe_20260926/claude/fila_REC'
DST.mkdir(parents=True, exist_ok=True)
cx, cy, R = 5375.786804312011, 3775.9774911631, 452.9785129274736; x0, y0, x1, y1 = 4677, 3077, 6077, 4477
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; t = np.clip((40 - d) / 10, 0, 1); w = t * t * (3 - 2 * t)
rep = {}
for f in sorted(SRC.iterdir()):
    o = DST / f.name
    if f.name in ('L56_G.npy',):
        if o.exists(): o.unlink()
        a = np.load(f); lid = f.name[1:3]; r = np.load(REC / f'L{lid}_G_moon.npy').astype(np.float64); v = a[y0:y1, x0:x1].astype(np.float64)
        n = np.rint(v + w * (r - v)).astype(np.uint16); dif = np.abs(n.astype(np.int32) - v.astype(np.int32))
        a[y0:y1, x0:x1] = n; np.save(o, a)
        rep[lid] = dict(px_canviats=int((dif > 0).sum()), dif_max=int(dif.max()), dif_max_d_mes_40=int(dif[d >= 40].max()), dif_max_d_30_40=int(dif[(d >= 30) & (d < 40)].max()))
    elif f.suffix == '.json': shutil.copy(f, o)
    elif not o.exists(): o.symlink_to(f)
(DST / 'C0_ESTAT_V105.json').write_text(json.dumps(rep, indent=1)); print(json.dumps(rep))
# ---- canal de la 56 per al PSB: a partir del canal REAL de la V104 (ja quantificat pel Photoshop), perquè fora de d < 40 px quedi byte a byte
import sys
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
p = PSB(str(R0 / '1-PHOTOSHOP/V104.psb')); a = p.channel(56, 1)[0].copy(); v = a[y0:y1, x0:x1].astype(np.float64)
r = np.load(REC / 'L56_G_moon.npy').astype(np.float64); n = np.rint(v + w * (r - v)).astype(np.uint16); a[y0:y1, x0:x1] = n
np.save(DST.parent / 'L56_G_V105_psb.npy', a); dif = np.abs(n.astype(np.int32) - v.astype(np.int32))
print('canal 56 per al PSB: px diferents de la V104', int((dif > 0).sum()), '· dif màx', int(dif.max()), '· a d ≥ 40:', int(dif[d >= 40].max()))
